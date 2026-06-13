# FID-VN-019 — L1b Phonological Alias Expansion (CT-042)
# Feature Intent Document | ISO_VN v1.0
# Status: APPROVE BY Andy feedback + CONS-20260612-001 (Groq + ChatGPT review)

| Field | Value |
|---|---|
| FID ID | FID-VN-019 |
| Layer | L1b (drug name correction) |
| LOC estimate | ~90-120 LOC (function + alias_map wiring, 4 rule groups) + ~60 LOC tests |
| Risk level | MEDIUM — touches FROZEN L1b alias_map, exact-match only (no new fuzzy logic) |
| Created | 2026-06-12 |
| Revised | v2 (2026-06-12) — Andy: cần research khoa học + thuật toán tổng quát hơn,
  không chỉ b/p; rule 4 split-by-region theo `docs/records/consultations/CONS-20260612-001.md`
  (Groq 80% confidence). v3 (2026-06-12) — ChatGPT review (88% confidence,
  APPROVE WITH CHANGES): Rule 2 thu hẹp xuống chỉ multi-syllable alias (dự đoán
  80% false-positive từ Rule 2 nếu không thu hẹp); vowel normalization + cluster/
  syllable-insertion gộp vào CT-053 (Vietnamese Medical Phonetic Encoder, Phase 2
  dài hạn, supersedes CT-052) thay vì mở rộng tiếp `_phonological_variants()`. |
| Approved by | Andy (via CONS-20260612-001, Groq + ChatGPT + Grok review) |
| Approved date | 2026-06-12 |

---

## WHY (Tại sao cần feature này?)

Andy quan sát thực nghiệm (pilot test, ghi ở CT-042): khi BS phát âm tên thuốc tiếng
Anh, PhoWhisper transcribe ra văn bản KHÔNG khớp ổn định với `phonetic_variants` đã
curate trong `drug_db_v200.json` — recall dao động mạnh tùy giọng BS (~20%→~50% trong
quan sát ban đầu của Andy với riêng hiện tượng b/p).

Andy phản hồi (2026-06-12): hiện tượng KHÔNG chỉ là b/p — "ÂM MŨI N,M NGƯỜI VIỆT
KHÔNG CÓ [giống tiếng Anh]" và yêu cầu tài liệu khoa học + thuật toán tổng quát hơn.
Sau khi research (Vietnamese-English contrastive phonology, xem nguồn dưới), bản FID
này được viết lại để cover **5 nhóm hiện tượng** có cơ sở ngôn ngữ học, không chỉ 1.

**Nguồn tham khảo** (academic, đọc 2026-06-12):
- [Interlanguage Phonology and the Pronunciation of English Final Consonant Clusters
  by Native Speakers of Vietnamese](https://www.academia.edu/3465003/Interlanguage_Phonology_and_the_Pronunciation_of_English_Final_Consonant_Clusters_by_Native_Speakers_of_Vietnamese)
- [Influence of Vietnamese Pronunciation on the Production of English Final Consonant
  Sounds](https://www.academia.edu/31932060/Influence_of_Vietnamese_Pronunciation_on_the_Production_of_English_Final_Consonant_Sounds)
- [Common mistakes in pronouncing English consonant clusters: A case study of
  Vietnamese learners (CTU Journal)](https://ctujs.ctu.edu.vn/index.php/ctujs/article/view/448)
- [Contrastive Analysis of Consonants in English and Vietnamese
  (ResearchGate)](https://www.researchgate.net/publication/352243293_Contrastive_Analysis_of_Consonants_in_English_and_Vietnamese)
- [The Adaptation of French Consonant Clusters in Vietnamese Phonology: An OT Account
  (J. Univ. Lang.)](https://www.sejongjul.org/archive/view_article?pid=jul-18-1-69)
- [Vietnamese phonology (Wikipedia)](https://en.wikipedia.org/wiki/Vietnamese_phonology)

**5 nhóm hiện tượng (xếp theo mức độ phổ biến/impact dự kiến lên drug names):**

1. **Aspiration neutralization (b/p, d/t, g/k/c)** — tiếng Việt không phân biệt âm vị
   bật hơi/không bật hơi như tiếng Anh (1 bộ phụ âm đầu ứng với p/b, t/d, k/g tiếng
   Anh). Đây là quan sát gốc của Andy — VẪN GIỮ trong thuật toán (đã có sẵn).

2. **Coda inventory restriction (m/n/ŋ/p/t/k CHỈ — "6 final consonants")** — tiếng
   Việt CHỈ cho phép 6 phụ âm cuối: /p, t, k, m, n, ŋ/ (không phát hành/unreleased).
   English có nhiều coda khác (z, s, v, f, dʒ, ʃ, θ, ð...) — KHÔNG tồn tại trong tiếng
   Việt ở vị trí cuối âm tiết. Đây chính là điều Andy nói "âm mũi n/m" — không phải
   tiếng Việt THIẾU m/n (tiếng Việt CÓ m/n/ng ở cuối), mà là **English dùng nhiều coda
   khác m/n/ng/p/t/k mà tiếng Việt không có**, nên BS Việt thường:
   - **Deletion** (chiến lược phổ biến nhất theo nghiên cứu) — bỏ hẳn phụ âm cuối
     không thuộc bộ 6 (vd "-ase"/"-ose" /s,z/ → rụng)
   - **Devoicing/closest-coda substitution** — thay bằng coda gần nhất trong bộ 6
     (vd /d/,/z/ cuối → /t/; /v/,/f/ cuối → /p/ hoặc rụng)

3. **Consonant cluster reduction** — tiếng Việt KHÔNG có cluster phụ âm (đầu hay
   cuối âm tiết). English cluster (vd "pred-NI-SONE" /sn/-like, "-stat-in" /st/) bị
   xử lý bằng (a) rụng 1 phụ âm trong cluster, hoặc (b) chèn nguyên âm đệm (epenthesis,
   vd "street"→"sơ-trit"). Với tên thuốc đã được phiên âm sẵn theo âm tiết tiếng Việt
   trong `phonetic_variants` (vd "xi pro phlo xa xin"), cluster trong TỪNG âm tiết
   phiên âm hiếm — nhưng cluster co thể xuất hiện ở BIÊN âm tiết khi ASR transcribe
   liền (vd "stat" → "sờ ta"/"xta"). → THUỘC PHASE 2 (xem RISKS R-PHON-05), KHÔNG
   implement trong FID này (combinatorial explosion cao, cần data thật để validate).

4. **/θ/, /ð/ → /t/, /d/ (hoặc /z/)** — tiếng Việt không có "th" (θ/ð). BS thường đọc
   "th" trong tên thuốc (ít gặp nhưng có, vd nhóm "Theo-" Theophylline) thành "t"/"đ".
   → thêm quy tắc: chuỗi con "th" ở đầu âm tiết → biến thể "t" (và "đ"/"d" sau
   `_normalize`).

5. **r/l/n merger ở đầu âm tiết** — /r/ và /l/ không phân biệt rõ trong nhiều giọng
   Việt; /r/ thường → /z/ hoặc /d/ (Nam), /l/ ↔ /n/ là hiện tượng phương ngữ Bắc Bộ
   nổi tiếng ("nói"/"lói"). → thêm quy tắc hoán đổi đầu âm tiết: r↔l, l↔n (độc lập
   với cặp aspiration #1).

**Reframe quan trọng (CONS-20260612-001, ChatGPT review v3)**: từ góc nhìn chính
xác hơn, L1b KHÔNG còn làm "phonological matching" thuần — vì ASR (PhoWhisper) đã
transcribe âm thanh thành MỘT CHUỖI CHỮ VIẾT TIẾNG VIỆT rồi (vd "mét rô ni đa dôn").
Bài toán thực chất là **"Vietnamese Orthography Matching"**: match 2 chuỗi chữ Việt
(transcript vs alias đã curate), trong đó sự khác biệt bắt nguồn từ các quy tắc
ngữ âm L1-transfer ở trên. `_phonological_variants()` vẫn là cách tiếp cận đúng
cho Phase 1 (enumerate biến thể chính tả), nhưng về dài hạn (155→1000 thuốc) nên
hướng tới phonetic-encoding (xem CT-053 dưới).

**Quyết định scope cho FID này (v3)**: implement #1 (đã có), #2-phần-deletion
(final consonant không thuộc {p,t,k,m,n,ng/nh} → sinh biến thể rụng, **CHỈ áp dụng
cho alias ≥2 âm tiết** — xem WHAT rule 2), #4, #5 — kết hợp được với limit "tối đa
2 âm tiết/alias" hiện có. KHÔNG implement #3 (cluster epenthesis) — và KHÔNG thêm
vowel normalization (đề xuất mới từ ChatGPT, xem dưới) — cả 2 gộp vào **CT-053**
(BACKLOG, Phase 2 dài hạn — Vietnamese Medical Phonetic Encoder, supersedes CT-052)
thay vì block FID này.

**Hiện tượng bổ sung từ ChatGPT review (KHÔNG implement trong FID này, → CT-053)**:
- **Vowel normalization**: biến đổi nguyên âm o/ô/ơ, i/inh, en/eng, an/ang (vd
  "metformin" → "mét pho min"/"mét phọc min"/"mét phô min") — đánh giá QUAN TRỌNG
  HƠN rule 4 (r/l/n) nhưng combinatorial risk cao hơn enumerate-based approach.
- **Syllable insertion / cluster breaking**: BS Việt thêm âm tiết đệm khi gặp
  cluster tiếng Anh (vd "statin"→"sờ ta tin", "steroid"→"xì tê rôi"). Cùng nhóm
  với #3 (cluster epenthesis), đánh giá hiệu quả lớn hơn rule 4.

**Hệ quả thực tế**: `drug_db_v200.json` đã có 155 thuốc × nhiều `phonetic_variants`
(vd Ciprofloxacin: "xi pro phlo xa xin"), nhưng chỉ ghi 1-2 cách viết cho mỗi biến thể
vùng miền — KHÔNG cover hết các hoán vị từ 4 nhóm hiện tượng trên mà ASR thực tế sinh
ra. Đây là gap khác với CT-027(5) (window size) — đây là gap về **bộ chữ cái** trong
mỗi alias, không phải số từ.

## WHAT (Feature làm gì? Input/Output?)

**Input**: `drug_db_v200.json` alias sources hiện có (`brands`, `name_variants`,
`phonetic_variants`) — KHÔNG sửa file JSON này.

**Output**: `_build_alias_map()` (`src/core/l1b_drug_correct.py`) sinh thêm các
**biến thể chính tả phonological** cho mỗi alias hiện có (brands/name_variants/
phonetic_variants — KHÔNG áp dụng cho INN gốc, để tránh đổi tên chuẩn), rồi thêm vào
`alias_map` như các key Layer-1 exact-match mới.

**Side effects**: alias_map lớn hơn (~155 drugs × trung bình ~10 alias × tối đa 8 biến
thể phonological/alias ≈ +10-12K key, vẫn O(1) dict lookup, `lru_cache(maxsize=1)`
không đổi). KHÔNG đổi `transcript`/output format, KHÔNG đổi `DrugMatch.match_layer`
(vẫn `1` — exact match).

### Quy tắc sinh biến thể (`_phonological_variants(alias: str) -> set[str]`)

Áp dụng trên chuỗi đã `_normalize()` (lowercase, bỏ dấu), theo TỪNG ÂM TIẾT
(space-separated token). 4 nhóm quy tắc, dựa trên research ở WHY (#1, #2, #4, #5):

1. **Aspiration onset hoán đổi** (nhóm #1 — đã có, giữ nguyên):
   - `b ↔ p` (vd "ba" ↔ "pa")
   - `d ↔ t` (vd "da" ↔ "ta")
   - `g ↔ k`, `c ↔ k` ở vị trí đầu âm tiết (vd "ga" ↔ "ka", "ca" ↔ "ka")

2. **Coda restriction — rụng phụ âm cuối thuộc nhóm voiced obstruent (z,v,d,đ) +
   "l"** (nhóm #2, MỞ RỘNG từ "final-l drop" cũ): nếu âm tiết kết thúc bằng phụ âm
   thuộc `{l, z, v, d, đ}` (KHÔNG mở rộng ra toàn bộ "ngoài {p,t,k,c,m,n,ng,nh}" như
   bản v2 — thu hẹp theo Grok round 3, ưu tiên voiced obstruent + "l" vì đây là 2
   case phổ biến nhất trong tên thuốc, vd "-zole"/"-mide"/"-vas") → sinh thêm biến
   thể RỤNG phụ âm cuối đó:
   - "...me tro ni đa zol" → "...me tro ni đa zo" (giữ ví dụ -zole cũ)
   Phụ âm cuối thuộc bộ {p,t,k,c,m,n,ng,nh} (coda hợp lệ tiếng Việt, ASR thường giữ
   nguyên) hoặc các phụ âm cuối khác (s,f,x...) → KHÔNG sinh biến thể rụng ở rule
   này (case khác → CT-053 nếu cần, sau khi có audio thật).

   **CONSTRAINT 1 (v3, theo ChatGPT review — Rule 2 dự đoán gây 80% false-positive
   nếu không thu hẹp)**: rule này CHỈ áp dụng khi **alias có ≥2 âm tiết** (≥2
   space-separated token). KHÔNG áp dụng cho alias 1 âm tiết — tức KHÔNG sinh
   alias_map key đứng riêng kiểu "zo"/"va"/"mi"/"te" (dù các key này có thể đã
   pass filter #7 "<3 ký tự"). Lý do: các token ngắn 2 ký tự này trùng rất nhiều
   với từ tiếng Việt phổ biến trong câu lâm sàng bình thường — nguy cơ FP cao hơn
   nhiều so với việc chúng xuất hiện như 1 âm tiết BÊN TRONG 1 alias đa âm tiết
   (context của các âm tiết khác trong cùng alias đã giảm collision risk).

   **CONSTRAINT 2 (v3, theo Grok round 3)**: xem quy tắc 8 (blacklist) — áp dụng
   cho TẤT CẢ rule 1-4, không riêng rule 2.

3. **"th" → "t"/"d" ở đầu âm tiết** (nhóm #4): nếu âm tiết bắt đầu bằng "th" (vd
   "theo" trong Theophylline) → sinh thêm biến thể thay "th" bằng "t" ("teo") và
   bằng "d" ("deo").

4. **r/l/n hoán đổi ở đầu âm tiết — SPLIT THEO VÙNG MIỀN** (nhóm #5, theo
   CONS-20260612-001 — Groq 80% confidence khuyến nghị split-by-region thay vì
   3-way đồng thời): `_build_alias_map()` biết alias thuộc region nào (key
   `phonetic_variants.{north,central,south}`, hoặc áp dụng cho TẤT CẢ region nếu
   alias từ `brands`/`name_variants` không gắn region):
   - Alias vùng **north** (hoặc không rõ region): hoán đổi `l ↔ n` (Bắc Bộ "nói/lói")
   - Alias vùng **central**/**south** (hoặc không rõ region): hoán đổi `r → l`
     VÀ `r → z` (KHÔNG hoán đổi ngược l→r, vì r hiếm trong cách đọc tiếng Việt)
   - KHÔNG áp dụng cả 2 cặp cùng lúc trên cùng alias (tránh 3-way explosion + giảm
     false-positive theo Groq's risk #1 "quy tắc không chính xác")

**Giới hạn & guard (giữ nguyên từ bản trước):**

5. **Giới hạn tổ hợp**: chỉ áp dụng các quy tắc 1-4 cho TỐI ĐA 2 âm tiết/alias (tránh
   combinatorial explosion trên alias 5-6 từ — ưu tiên âm tiết ĐẦU và CUỐI, nơi sai
   khác phổ biến nhất theo nghiên cứu/quan sát)
6. **Ambiguity guard**: khi thêm 1 biến thể sinh ra vào `alias_map`, nếu key đã tồn
   tại và map sang INN KHÁC → **SKIP** (không overwrite, không thêm), ghi
   `logger.debug` để theo dõi số lượng collision (kỳ vọng phiên benchmark sẽ log ra
   con số cụ thể)
7. Biến thể quá ngắn (<3 ký tự sau khi bỏ space) → SKIP, theo nguyên tắc filter hiện
   có (CE-103/CT-049: tránh match nhầm từ tiếng Việt phổ biến)
8. **Blacklist từ tiếng Việt phổ biến (v3, theo Grok round 3)**: hardcode 1 set
   ~30-50 từ/âm tiết tiếng Việt thông dụng trong câu lâm sàng (vd "có", "không",
   "đau", "mệt", "về", "với", "này", "mi", "va", "teo", "te", "no", "lo"...) —
   sống trong `src/core/l1b_drug_correct.py` hoặc file data riêng. Nếu BẤT KỲ
   token nào trong biến thể sinh ra (rule 1-4) nằm trong blacklist này → SKIP
   biến thể đó (không thêm vào alias_map), kể cả khi đã pass rule 5+7.

### Ví dụ

`phonetic_variants.north` của Ciprofloxacin có "xi pro phlo xa xin" (5 từ, đã match
được nhờ CT-051). Vì alias thuộc region `north` → quy tắc 4 áp dụng `l ↔ n` cho âm
tiết "phlo" → "phno" (không áp dụng r→l/r→z vì là alias `north`); quy tắc 1 không
đổi "xi"/"xin" (không trong bộ b/p/d/t/g/k/c).

Metronidazole "me tro ni đa zôl" (north) — âm tiết cuối "zôl" → `_normalize` =
"zol" → quy tắc 2 sinh "me tro ni đa zo" (rụng "l" cuối, vì "l" không thuộc bộ coda
hợp lệ); quy tắc 1 trên "đa"→"ta" sinh "me tro ni ta zol"/"me tro ni ta zo" (kết hợp
quy tắc 1+2, giới hạn 2 âm tiết: âm tiết cuối áp cả 2 quy tắc).

Theophylline "theo phi lin" — quy tắc 3 sinh "teo phi lin"/"deo phi lin".

## ACCEPTANCE CRITERIA (Khi nào gọi là DONE?)

- [x] `_phonological_variants()` implemented + unit tests (sinh đúng biến thể, giới
  hạn 2 âm tiết, bỏ biến thể <3 ký tự)
- [x] `_build_alias_map()` wire `_phonological_variants()` cho brands/name_variants/
  phonetic_variants (KHÔNG cho INN gốc), với ambiguity-guard (skip collision)
- [x] Test: alias collision giữa 2 INN khác nhau → SKIP, không ghi đè (test giả lập
  2 alias cố ý đụng nhau) — `test_alias_map_collision_skipped`
- [x] Test end-to-end: garble có phụ âm hoán đổi (vd "me tro ni ta" — South
  phonetic_variant "me tro ni đa" + rule1 đ→t) → match đúng Metronidazole qua
  Layer 1 — `test_metronidazole_consonant_swap_garble`
- [x] 973/973 tests PASS (958 cũ + 15 mới), bandit 0 HIGH
- [x] **A/B benchmark trên branch `experiment/fid-vn-019-phonological` TRƯỚC khi
  merge** — `tools/bench_002b.py` (57 clips real BS voice, BENCH-002b):
  - alias_map: 1028 → 1913 keys (+885, ~+86%), 21 phonological collisions skipped
    (ambiguity guard)
  - Drug Recall: 0.556 → 0.556 — KHÔNG GIẢM so với baseline 55.6% ✅ PASS
  - Drug Precision: 0.714 → 0.714 — KHÔNG ĐỔI so với master HEAD hiện tại (verified
    bằng cách chạy lại bench trên master HEAD `l1b_drug_correct.py` với cùng eval
    data → cũng ra 0.714/FP=2) ✅ PASS, 0 FP mới từ phonological alias
  - LƯU Ý: committed baseline `data/eval/bench_002b_results.json` (precision
    0.833/FP=1) ĐÃ STALE từ trước (Oresol FP trên REF_HN_P1_Clip3, không liên quan
    FID này) → CT-054 (BACKLOG) để regenerate baseline + debug riêng
  - Kết quả lưu: `data/eval/bench_002b_phon_results.json`
- [x] CHANGELOG entry + Andy approve merge vào `master` sau khi xem A/B kết quả
- [x] **CT-053 — Vietnamese Medical Phonetic Encoder** thêm vào
  `docs/records/BACKLOG.md` (Phase 2 dài hạn — cluster epenthesis + vowel
  normalization + syllable insertion, supersedes CT-052, không block FID này)

## RISKS

| Risk ID | Mô tả | Kiểm soát |
|---|---|---|
| R-PHON-01 | Biến thể hoán đổi (vd "ba"→"pa") trùng với từ tiếng Việt phổ biến → false positive trên câu lâm sàng bình thường. ChatGPT review: Rule 2 (coda drop) dự đoán là nguồn FP lớn nhất (~80%) nếu sinh key 1-âm-tiết đứng riêng (vd "zo","va","mi","te") | Filter <3 ký tự (#7) + ambiguity guard (#6) + **Rule 2 chỉ áp dụng cho alias ≥2 âm tiết (v3)** + A/B benchmark Drug Precision trước merge |
| R-PHON-02 | 2 thuốc khác nhau sinh ra biến thể giống nhau (collision) → 1 trong 2 bị mất alias đúng | Ambiguity guard SKIP cả 2 (không gán cho bên nào) — an toàn hơn là gán sai; log để Andy review danh sách collision |
| R-PHON-03 | alias_map tăng kích thước đáng kể → tăng thời gian `_build_alias_map()` (chạy 1 lần, `lru_cache`) | Giới hạn 2 âm tiết/alias (#3); đo thời gian build trước/sau trong A/B |
| R-PHON-04 | Thay đổi alias_map ảnh hưởng Layer 2 fuzzy (dùng `full_alias` làm fallback) — alias mới có thể đổi kết quả fuzzy top-2/ambiguity gate | Test `TestAmbiguityGate` hiện có (`tests/unit/test_l1b_drug_correct_v2.py`) phải vẫn PASS không đổi |
| R-PHON-05 | Consonant cluster reduction/epenthesis (nhóm #3) + vowel normalization + syllable insertion (ChatGPT review v3) KHÔNG implement trong FID này — vẫn là gap chưa cover | Ghi **CT-053 — Vietnamese Medical Phonetic Encoder** vào `docs/records/BACKLOG.md` (Phase 2 dài hạn, supersedes CT-052 — hướng Soundex/Metaphone-style encoding, cần audio thật để validate trước khi thiết kế) |

## TESTS REQUIRED

- [x] `tests/unit/test_l1b_phonological.py` (mới):
  - `test_phon_variants_b_p_swap` — "ba" sinh "pa" và ngược lại
  - `test_phon_variants_d_t_swap`, `test_phon_variants_g_k_c_swap`
  - `test_phon_variants_coda_drop_multisyllable` — alias ≥2 âm tiết, vd
    "me tro ni đa zol" → "...đa zo" (rụng coda ngoài bộ {p,t,k,c,m,n,ng,nh})
  - `test_phon_variants_coda_drop_single_syllable_skipped` — alias 1 âm tiết (vd
    "zol" đứng riêng) → KHÔNG sinh biến thể rụng "zo" (constraint v3, tránh FP)
  - `test_phon_variants_coda_keep_valid` — "tin"/"min"/"pin" (coda hợp lệ) KHÔNG
    sinh biến thể rụng
  - `test_phon_variants_th_to_t_d` — "theo" sinh "teo" và "deo"
  - `test_phon_variants_r_l_n_swap_north` — alias region `north`: "no" sinh "lo"
    (l↔n), KHÔNG sinh biến thể r→l/r→z
  - `test_phon_variants_r_l_n_swap_south` — alias region `south`/`central`:
    "ro" sinh "lo" và "zo" (r→l, r→z), KHÔNG hoán đổi l↔n
  - `test_phon_variants_limit_2_syllables` — alias 5 từ chỉ áp dụng ở âm tiết đầu/cuối
  - `test_phon_variants_min_length_filter` — biến thể <3 ký tự bị loại
  - `test_alias_map_collision_skipped` — 2 alias giả định đụng nhau → cả 2 KHÔNG có
    trong alias_map (hoặc giữ nguyên bản gốc, không bị overwrite)
  - `test_phon_variants_blacklist_skipped` — biến thể chứa token trong blacklist
    (vd "mi", "va", "teo") → SKIP, không thêm vào alias_map dù pass filter khác
- [x] `tests/unit/test_l1b_drug_correct_v2.py` — thêm vào `TestLayer1Exact`:
  - `test_metronidazole_consonant_swap_garble` (vd "me tro ni ta", từ South
    phonetic_variant "me tro ni đa")
  - `test_theophylline_th_garble` (vd "teo phylli ne" → Theophylline)
- [x] Toàn bộ 958/958 hiện có PASS không đổi (regression guard) — 973/973 total
- [x] A/B: `tools/bench_002b.py` chạy lại trên branch, output JSON lưu
  `data/eval/bench_002b_phon_results.json` để so sánh với
  `data/eval/bench_002b_results.json` (baseline)

## COMMIT FORMAT

```
feat(l1b): phonological alias expansion b/p d/t g/k/c + final-l drop [FID-VN-019]
```

---

*FID Template | ISO_VN v1.0 | MediVoice VN*
*File: fids/FID-VN-019.md*
