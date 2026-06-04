"""
MediVoice AI — Ghi âm test audio tiếng Việt
Chạy: python tools/record_test_audio.py
Lưu:  data/audio/test_viet_01.wav ... test_viet_10.wav
"""

import os
import sounddevice as sd
import soundfile as sf
import numpy as np

SAMPLE_RATE = 16000   # Whisper yêu cầu 16kHz
CHANNELS    = 1
OUTPUT_DIR  = os.path.join("data", "audio")

SENTENCE_SETS = {
    "medivoice": [
        "Bệnh nhân nam 52 tuổi, đau ngực trái từ sáng, lan lên vai, mồ hôi nhiều.",
        "Huyết áp 158 trên 95, mạch 88, đang dùng lisinopril 10 mg nhưng không đều.",
        "Bệnh nhân nữ 34 tuổi đến vì ho khan 3 tuần nay, thử thuốc ho không bớt.",
        "Tiểu đường type 2, HbA1c lần này 8.9, tăng metformin lên 1000 mg hai lần mỗi ngày.",
        "Đau đầu buổi sáng, kèm mờ mắt thoáng qua, không có tiền sử tăng huyết áp.",
        "Bệnh nhân 67 tuổi, té ngã ở nhà, đau hông phải, đi khập khiễng, cần chụp X-quang.",
        "Tái khám sau mổ ruột thừa, vết thương lành tốt, không sốt, ăn uống bình thường.",
        "Trẻ 8 tuổi, sốt 38.5, đau họng 2 ngày, amoxicillin 250 mg uống 3 lần mỗi ngày.",
        "Bệnh nhân lo lắng, mất ngủ 1 tháng, không muốn dùng thuốc, muốn thử liệu pháp khác trước.",
        "Khỏe mạnh, không triệu chứng, đến khám định kỳ, kết quả máu bình thường.",
    ],
    "dental": [
        "Bệnh nhân nữ 28 tuổi, đau răng số 6 hàm dưới bên phải, đau nhiều khi nhai.",
        "Sâu răng sâu gần tủy, cần điều trị tủy trước khi phục hình.",
        "Bệnh nhân 45 tuổi, nướu sưng đỏ vùng răng cửa hàm trên, chảy máu khi chải.",
        "Răng khôn số 8 hàm dưới bên trái mọc lệch, chèn vào răng số 7, đề nghị nhổ.",
        "Chụp X-quang panoramic, mất xương ổ răng khoảng 30 phần trăm, viêm nha chu độ 2.",
        "Bệnh nhân 12 tuổi, răng vĩnh viễn đang mọc, cần chỉnh nha, hẹn tư vấn niềng.",
        "Trám composite răng số 4 hàm trên bên trái, sâu mặt nhai, kích thước nhỏ.",
        "Bệnh nhân tiểu đường, nướu lành chậm, kháng sinh amoxicillin 500 mg trước khi nhổ.",
        "Mòn răng cổ do chải quá mạnh, tư vấn đổi bàn chải mềm và kỹ thuật chải đúng.",
        "Răng số 21 gãy một phần do tai nạn, tủy còn sống, làm mão sứ kim loại.",
    ],
}


def record_one(filename: str, sentence: str, index: int) -> None:
    print(f"\n{'─'*60}")
    print(f"[{index}/10] {sentence}")
    print(f"{'─'*60}")
    input("  → Nhấn ENTER để bắt đầu ghi âm...")

    frames = []

    def callback(indata, frame_count, time_info, status):
        frames.append(indata.copy())

    print("  🔴 Đang ghi... nhấn ENTER để dừng.")
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                        dtype="float32", callback=callback):
        input()

    audio = np.concatenate(frames, axis=0)
    sf.write(filename, audio, SAMPLE_RATE)
    duration = len(audio) / SAMPLE_RATE
    print(f"  ✅ Lưu: {filename}  ({duration:.1f}s)")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("MediVoice AI — Ghi âm test tiếng Việt (10 câu)")
    print("Mỗi câu: nhấn ENTER để bắt đầu → đọc câu → nhấn ENTER để dừng")
    print("=" * 60)

    sets = list(SENTENCE_SETS.keys())
    print(f"\nChọn bộ câu: {' / '.join(sets)}")
    topic = input("→ ").strip().lower()
    if topic not in SENTENCE_SETS:
        print(f"Không hợp lệ. Dùng mặc định: {sets[0]}")
        topic = sets[0]

    sentences = SENTENCE_SETS[topic]

    skip_existing = input("\nBỏ qua file đã tồn tại? (y/n, mặc định y): ").strip().lower()
    skip_existing = skip_existing != "n"

    for i, sentence in enumerate(sentences, start=1):
        filename = os.path.join(OUTPUT_DIR, f"test_{topic}_{i:02d}.wav")
        if skip_existing and os.path.exists(filename):
            print(f"\n[{i}/10] Bỏ qua (đã có): {filename}")
            continue
        record_one(filename, sentence, i)

    print("\n" + "=" * 60)
    print(f"Xong! {len(sentences)} file WAV trong {OUTPUT_DIR}/")
    print(f"File: test_{topic}_01.wav ... test_{topic}_10.wav")
    print("=" * 60)


if __name__ == "__main__":
    main()
