# 𝕏推薦アルゴリズム完全解析（2026年8月版）

- 解析対象: [xai-org/x-algorithm](https://github.com/xai-org/x-algorithm)（コミット `d0cef2f`、2026年8月14日更新版、全2,024ファイル）
- 解析日: 2026-08-21
- 解析方法: サブエージェント7体による全サブシステム精読 + 主要数値のソースコード直接検証
- 本ドキュメントは `docs/x-algorithm-guide.html`（一般向けガイド）の技術的裏付け資料

> **注意**: リポジトリの値はcronで本番のfeature switch値に同期されたスナップショット。一部ルール（Groxプロンプト、botmakerルールの一部、BDSMの発動閾値、AESの本番閾値）は意図的に非公開。`enforcement_user.yaml`の`follower_count >= 12.34`は「ゲーミング防止のためのダミー値」と明記されている。

---

## 1. 全体構造

```
リクエスト（フィードを開く）
  ↓ HOME MIXER (home-mixer/)
  ① クエリハイドレーション: 行動履歴(最大1024件)・フォロー・ブロック/ミュート・既読など19種
  ② 候補ソース(並列):
     - Thunder(フォロー中/保持2日/最大1200件)
     - Phoenix retrieval(フォロー外/最大1000件)
     - SimClusters(フォロー外/最大800件)
  ③ 候補ハイドレーション
  ④ プレスコアフィルター 17種（順序固定）
  ⑤ スコアリング: PhoenixScorer → RankingScorer → VMRanker(DPP)
  ⑥ TopKScoreSelector: 上位50件
  ⑦ ポストセレクションフィルター: VFFilter → AncillaryVFFilter → DedupConversationFilter
  ⑧ 最終35件 → ブレンド(広告/Who to Follow[6位]/プロンプト)
```

- 最終表示: `RESULT_SIZE = 35`、選抜: `TOP_K_CANDIDATES_TO_SELECT = 50`（`home-mixer/params/config.rs`）
- ランキング（順位決定）と可視性フィルタリング（表示可否）は完全に別システム

## 2. スコアリング重み（home-mixer/params/param.rs、検証済み）

`最終スコア = Σ (weight_i × P(action_i))` — 重みは**予測確率**に掛かる。実際の件数ではない。
（公式注記: 「通報1件=いいね468個分」という読み方は誤り。Reportの基準確率はLikeの1/1000以下なので重みが大きい）

### 正の重み
| アクション | 重み |
|---|---|
| リンクコピーで共有 (ShareViaCopyLink) | **20.0** |
| 返信 (Reply) | **5.0**（相互フォロー著者のオリジナル投稿は +15.0 → 実質 **20.0**） |
| 引用 (Quote) | **5.0** |
| DMで共有 (ShareViaDm) | **5.0** |
| 投稿者をフォロー (FollowAuthor) | **4.0** |
| 共有ボタン (Share) | **2.0** |
| リポスト (Retweet) | **1.0** |
| いいね (Favorite) | **0.5** |
| クリック (Click) | **0.4** |
| リンクを開く (OpenLink) | **0.2** |
| 写真拡大 / 動画再生 / 動画良質視聴VQV | **0.05**（VQVは動画10秒超のみ。閲覧者のフォロワー1万以上だと0） |
| 滞在時間 (ContDwellTime) | **0.004/秒** |
| 未探索投稿 (PostUnexplored) | 0.02（フォロー内のみ） |
| プロフィールクリック / 離散Dwell / 引用先VQV | 0.0（無効化中） |

### 負の重み
| アクション | 重み |
|---|---|
| 通報 (Report) | **-234.0** |
| ミュート (MuteAuthor) | **-58.8** |
| 興味なし (NotInterested) | **-43.2** |
| ブロック (BlockAuthor) | **-31.2** |
| 滞在せずスクロール (NotDwelled) | **-0.02** |

### スコア後の補正（適用順）
1. **新規投稿者ブースト** (author_cold_start.rs): フォロワー≦1,000・表示回数<1,000・投稿24時間以内のオリジナル投稿から1リクエスト1件を15〜16位相当のスコアまで引き上げ（下限保証方式=既にそれ以上なら変化なし）。補足: 元スコアが上位85%以内（`LowImpressionsMaxPositionRatio=0.85`）の候補のみ対象。A/B実験（MoE Codivert）の枠組み内で運用されており、24時間鮮度条件はTreatmentアーム限定。`EnableViewerColdStart`デフォルトtrue、RankingScorerから無条件に呼ばれる
2. **著者多様性減衰**: 同一著者のk番目(0始まり) → `(1-0.25)×0.5^k+0.25`倍。2件目0.625倍、3件目0.4375倍、下限0.25倍
3. **フォロー外割引 (OON)**: ×**0.75**。フォロー中アカウントでも**リプライ・リポストには適用**（デフォルト有効）。トピック指定時は×0.5。新規閲覧ユーザー向け`NEW_USER_OON_WEIGHT_FACTOR=0.00001`（条件: フォロー5人以上かつアカウント年齢<閾値）は存在するが、閾値`NewUserAgeThresholdSecs`のデフォルトが0のため**現行デフォルトでは発火しない**（実験用）
4. **VMRanker (DPP)**: theta=0.65、上位150件プール内で埋め込み類似の投稿を間引き（同一内容はスコア最高の1件のみ生き残る）

### 双方向ブースト変遷 (docs/BIDIRECTIONAL_BOOST_CHANGE.md)
2026-07-10 実験開始(5/10/15/20) → 07-13 広範展開(20.0) → 07-24 調整(**15.0**、現行)

## 3. プレスコアフィルター（実行順、home-mixer/filters/）

1. DropDuplicates → 2. CoreDataHydration → 3. **Age(48時間超を除外)** → 4. SelfTweet → 5. **OONRetweetReply(フォロー外へのRT/リプライ配信禁止)** → 6. OONNsfwSimclusters → 7. RetweetDeduplication → 8. IneligibleSubscription → 9-11. 既読/配信済み(直近10分100件) → 12. ミュートキーワード → 13. AuthorSocialgraph(ブロック/ミュート) → 14. Brazil2026Election(665アカウント、フォロワーには表示) → 15. Video → 16. TopicIds → 17. NewUserMinEngagement(デフォルト無効)

ポストセレクション: VFFilter(可視性DROP除去) → AncillaryVF(親/引用元/RT元がDROPなら連座) → **DedupConversation(同一スレッドから最高スコア1件のみ)**

## 4. Phoenixモデル（phoenix/）

- **ランキング**: Transformer 8層・埋め込み2560次元・履歴1022件・候補64件。候補分離アテンション（候補同士は互いを見ない→スコアはバッチ非依存）。ハッシュ埋め込み（語彙辞書なし、新規投稿も即表現可能）
- 予測対象: 約60種の行動（fav/reply/quote/retweet/report/not interested/block/mute/dwell/video系/ブックマーク/スクショ/プロフクリック等）+ 滞在時間回帰
- 学習時マスク: 通報・興味なし等の強い拒否があるとポジティブラベルは全て0に上書き
- **リトリーバル**: Two-Tower内積検索。**正例は「いいね」のみ**。通報/興味なし/ブロック/ミュート等が1つでもあれば正例から除外
- 投稿は本文テキストではなく**セマンティックID**（マルチモーダル埋め込みの残差量子化 6レベル×256コード）+著者ハッシュで表現 → 「同じ意味の投稿」はモデル上近くなる

### phoenix-rankall（検索インデックス管理）
- 投稿作成で`post_creation`インデックス(24時間)に無条件掲載
- **いいね1件**で`1fav`インデックス(24-48h)へ。**投稿後49時間を過ぎるといいねイベントでのインデックス追加は停止**
- **いいね32件**で`32fav`(高品質バケット)へ昇格。再評価トリガーは2の冪(1,2,4,8,16,32…)
- **リプライ・リポスト・コミュニティ投稿はインデックス対象外**（引用は対象）
- VF DROP判定/NSFW判定はインデックスから除外
- **動画(10秒超)は専用インデックスで最長30日**、evergreen枠は最長5年。テキストは24-48時間
- **フォロワー1,000人未満は`tail`専用インデックス**（いいね0件でも24時間掲載）

## 5. SimClusters（コミュニティクラスタ拡散）

- 週次バッチで約14.5万クラスタ（アクティブフォロワー400人以上の上位2,000万ユーザー）
- **投稿の埋め込み永続化には合計いいね8件が必要**（`MinFavoriteCount = 8`）
- クラスタスコアは**8時間半減**の指数減衰（`HalfLife = 8.hours`）
- スコアは「誰がいいねしたか」で決まる: いいねした人の所属クラスタの重みが投稿に加算 → **クラスタ内シェアが効く**（絶対数より密度）
- 自分の投稿への自己いいねは除外。候補は投稿後48時間以内のみ

## 6. 可視性フィルタリング（visibility-filtering/）

3応答: ALLOW / INTERSTITIAL(ぼかし) / DROP。ルールは上から順に評価、最初のDROPで即確定。

- **共通28ルール**（フォロワーにも適用=完全非表示）: 凍結/退会/鍵/ブロック/ミュート、投稿ラベル `SPAM`・`PDNA`・`BOUNCE`・`FOSNR_*`(ヘイト/暴力発言/虐待/選挙妨害)、法的削除、未成年NSFW制限など
- **おすすめ専用+26ルール**（フォロワーには見える=シャドウバン実体）: `SPAM_HIGH_RECALL`(投稿/アカウント両方)、`DO_NOT_AMPLIFY`、NSFW系ラベル全種、`IMPERSONATION_HIGH_PRECISION`(なりすまし)、`COMPROMISED`(乗っ取り)、`ABUSIVE_HIGH_RECALL`など
- INTERSTITIAL: `NSFW_HIGH_PRECISION`・`GORE_AND_VIOLENCE_HIGH_PRECISION`等（閲覧者設定依存）
- 障害時はフェイルオープン（表示側に倒れる）

## 7. ラベルが付く行動（botmaker-rules/ + abuse-enforcement-service/）

| 行動 | ラベル | 期間 |
|---|---|---|
| 評判の悪いURL(BAD/LOW_QUALITY)を投稿・ピン留め | SPAM / SPAM_HIGH_RECALL | 7日〜 |
| UNSAFE判定URL | SEARCH_BLACKLIST + DO_NOT_AMPLIFY + UNSAFE_URL + MALICIOUS_URL | — |
| 非フォロワーへのメンション+低品質URL | SPAM_HIGH_RECALL | — |
| 酷似テキストの大量投稿(コピペ) | COPYPASTA_SPAM | — |
| バズ投稿への便乗リプライ(Groxスパムスコア≥0.97) | RISKY_HIGH_VIZ_REPLY | 14日 |
| いいね比の通報率が高い(Agatha >0.9975等) | AGATHA_SPAM / AGATHA_SPAM_TOP_USER | 7日 |
| LLM生成量産文(llm_slop) | SpamHighRecall | 30日 |
| 意味不明文字列(gibberish) / 高速リプライ | SpamHighRecall | 30日 |
| 直近5投稿中3投稿がNSFW高精度判定 | アカウントにNSFW_HIGH_PRECISION | 7日 |
| ボット的行動(BDSM 8ヘッド検出) | 凍結/チャレンジ/SpamHighRecall | — |
| CSE(児童搾取)関連 | 即・永久凍結 | 永久 |

- Agathaの比率スコア分母は**フォロー外からのいいねのみ**。1人の加害者のブロック/通報は最大100件までしかカウントされない
- 高PageRank判定アカウントは自動ラベリング対象外→人間レビューへ。判定ロジック（IsHighPageRankUser.df）: UserCredV2スコアの**データがある場合はPageRank基準のみ**（閾値`HighPageRankThreshold`の値はリポジトリ内に定義なし=非公開）、**データがない場合のみフォロワー数25,000超**のフォールバック基準を使用
- BDSM検出対象: FollowBot、LikeBot、EngagementAmplifier、ReplySpamBot、TweetSpamBot、RTBot、MultiActionBot（発動閾値は非公開・センチネル値9.99に置換済み）
- 執行はGrowthBook動的コンフィグが本番ソース（リポジトリはスナップショット）

## 8. 信用スコア（user-cred-v2/）

- フォローグラフ+直近7日のエンゲージメントエッジ上のPersonalized PageRank
- `score = clamp(165.2 + 7.07 × ln(mass), 0, 100)`
- テレポート先は認証済み(Premium/組織)アカウントに偏る設計
- スパム判定(near-zero)ユーザーのフォローは他者のスコアに寄与しない
- **多重アカウント(Linked Users)間のエッジは全経路から除外**（複垢相互応援は無効）

## 9. コンテンツ理解（grox/ ほか）

- Grok系LLMが投稿時に分類: 大分類10種（Spam, AdultContent, HateOrAbuse, ViolentSpeech, ViolentMedia, ChildSafety, SuicideOrSelfHarm, IllegalAndRegulatedBehaviors, TerrorismOrViolentExtremism, CivicIntegrity）
- スパム細分類9種: EngagementFarming, EngagementTrading, FinancialScam, HashTagAbuse, ScamLinks, BotProduced, PlatformManipulation, EngagementBaiting, CardManipulation, MentionAbuse
- LLMプロンプト(.j2)は非公開
- NSFW判定は画像だけでなく投稿者の前歴スコア・フォロワー層のNSFW傾向・フォロワー数も入力（pnsfwmedia）

## 10. 透明性ツール

- **Under the Hood**: https://x.com/i/under_the_hood — 自分のアカウント/投稿のラベルの月次集計を確認可能（アカウント年齢365日以上・月10投稿以上・月末から10日後に公開）
- 公開対象は投稿ラベル17種+アカウントラベル11種のホワイトリスト方式

## 11. フォロワー数で挙動が変わる全ポイント（2026-08-21 再スイープで確定）

リポジトリ全体をフォロワー数関連で再グレップし、全サブREADME（実在するのは トップレベル / bdsm / phoenix / phoenix/reference の4件のみ。home-mixer等のサブREADMEは存在しない）を精読した結果。

| 閾値 | 対象 | 挙動 | 出典 |
|---|---|---|---|
| **≦100人** | 投稿者 | SimClustersの**プロデューサー埋め込み対象外**（`minNumFollowersForProducer=100`・`minNumFaversForProducer=100`。フォロワー数>100が必要）。この経路での発見可能性が構造的に低い | simclusters/.../ProducerEmbeddingsFromInterestedIn.scala:473 |
| **<1,000人** | 投稿者 | **tail専用インデックス**にいいね0でも24時間掲載（ロングテール救済。`TAIL_MAX_AUTHOR_FOLLOWERS=1000`、`followers >= 1000`で除外） | phoenix-rankall/src/processor/sid_tail_processor.rs |
| **≦1,000人** | 投稿者 | **新規投稿者ブースト**対象（§2参照） | home-mixer/scorers/author_cold_start.rs |
| **<1,000人** | スレッド主 | ルート著者のフォロワー<1,000のスレッドは**協調スパム検知の対象外**（"low_blast_radius"） | grox/flows/reply_spam/task_filter.py:97 |
| **≦60,000人** | 会話の親/ルート著者 | リプライの**スパム検知スコアリング対象**。**60,000超では代わりにLLM返信ランキング**（重要な返信の並べ替え）が働く（`FOLLOWER_COUNT_THRESHOLD_FOR_SPAM_DETECTION/REPLY_RANKING = 60000`） | grox/flows/reply_spam/task_filter.py:17,185 |
| **>25,000人** | 投稿者 | 自動ラベリング免除のフォールバック基準（PageRankデータがない場合のみ。§7参照） | botmaker-rules/.../IsHighPageRankUser.df |
| **≧10,000人** | **閲覧者** | 動画品質視聴（VQV）重みが強制0（大規模アカウントの視聴は動画スコアに寄与しない。引用内動画のquoted_vqv_weightにはこの制限なし） | home-mixer/util/candidates_util.rs:4 |
| **100,000人** | 投稿者 | Grox LLMプロンプト上の「大規模アカウント」定義（`large_account_follower_threshold`） | grox/flows/reply_spam/prompts.py |
| （非公開） | 投稿者 | abuse-enforcement-serviceの高フォロワー執行免除。リポジトリ上の`follower_count >= 12.34`は「ゲーミング対策のモック値」と明記、本番閾値は非公開 | abuse-enforcement-service/.../enforcement_user.yaml:18 |
| （非公開） | 投稿者 | BDSM（ボット検知）には「これ未満ではスコアリング自体が発火しないアカウント規模フロア」（min-actionsゲート）が存在、値はセンチネル999999に置換済み | bdsm/README.md:104-115 |
| 集計区分 | — | Under the Hood内部のフォロワー階層: `<1K` / `1K-10K` / `10K-100K` / `≧100K` | under-the-hood/scalding/UnderTheHoodCommon.scala:51 |

## 12. Thunder（フォロー中ソース）詳細

- 投稿保持期間: **2日**（172,800秒）。返却は新着順のみ（スコアリングなし）
- 1著者あたり上限: オリジナル50件/リプライ30件/動画100件
- 動画枠: メディア1件のみ・**5秒以上**。リプライは動画枠対象外
- フォロー外への3階層目以降の返信チェーンは非表示
