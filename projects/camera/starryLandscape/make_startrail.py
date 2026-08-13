from PIL import Image, ImageFilter
import numpy as np
import os
import sys
import subprocess


# ============================================================
# 固定設定
# ============================================================

REFERENCE_COUNT = 51
TEST_COUNT = 5

WIDTH = 5304
HEIGHT = 7952

REFERENCE_FILENAME = "mountain_reference.jpg"
MASK_FILENAME = "mountain_mask_preview.jpg"
TEST_FILENAME = "test_5frame_mountain.jpg"

FRAME_DIR_NAME = "star_frames"
VIDEO_FILENAME = "startrail_24fps.mp4"


# ============================================================
# ユーティリティ
# ============================================================

def abort(message="処理を中止しました。"):
    print()
    print(message)
    sys.exit(0)


def error(message):
    print()
    print("=" * 60)
    print("ERROR")
    print("=" * 60)
    print()
    print(message)
    print()
    sys.exit(1)


def confirm(message):
    print()
    print("=" * 60)
    print(message)
    print("=" * 60)
    print()
    print("[Enter] → 次のフェーズへ")
    print("[q]     → 中止")

    answer = input("> ").strip().lower()

    if answer == "q":
        abort()


def check_image_size(filename):
    try:
        with Image.open(filename) as img:
            return img.size
    except Exception as e:
        error(
            f"画像を読み込めませんでした。\n"
            f"{filename}\n\n"
            f"{e}"
        )


# ============================================================
# 起動
# ============================================================

print()
print("=" * 60)
print("星景タイムラプス作成")
print("=" * 60)
print()


# ============================================================
# JPEGディレクトリ入力
# ============================================================

while True:

    jpeg_dir = input(
        "JPEG画像が保存されているディレクトリを入力してください。\n"
        "例: /Users/ronowe55/Pictures/jpeg\n\n"
        "JPEG_DIR > "
    ).strip()

    # 前後のクォートを除去
    jpeg_dir = jpeg_dir.strip("\"'")

    if not jpeg_dir:
        print()
        print("ディレクトリを入力してください。")
        print()
        continue

    jpeg_dir = os.path.abspath(
        os.path.expanduser(jpeg_dir)
    )

    if not os.path.isdir(jpeg_dir):

        print()
        print(
            f"ディレクトリが存在しません:\n"
            f"{jpeg_dir}"
        )
        print()
        continue

    break


# ============================================================
# START / END入力
# ============================================================

while True:

    try:

        START = int(
            input(
                "\n元画像の開始番号を入力してください。\n"
                "例: 8986\n\n"
                "START > "
            ).strip()
        )

        END = int(
            input(
                "\n元画像の終了番号を入力してください。\n"
                "例: 9136\n\n"
                "END > "
            ).strip()
        )

    except ValueError:

        print()
        print("番号は数字で入力してください。")
        print()
        continue

    if START >= END:

        print()
        print(
            "STARTはENDより小さくしてください。"
        )
        print()
        continue

    break


TOTAL = END - START + 1


# ============================================================
# 出力ディレクトリ入力
# ============================================================

default_output_dir = os.path.join(
    jpeg_dir,
    "startrail_output"
)

print()
print(
    "出力ディレクトリを指定してください。"
)
print(
    "何も入力しない場合:"
)
print(
    f"  {default_output_dir}"
)
print()

output_input = input(
    "OUTPUT_DIR > "
).strip()

output_input = output_input.strip("\"'")

if output_input:

    output_dir = os.path.abspath(
        os.path.expanduser(output_input)
    )

else:

    output_dir = default_output_dir


os.makedirs(
    output_dir,
    exist_ok=True
)


# ============================================================
# 出力パス
# ============================================================

reference_file = os.path.join(
    output_dir,
    REFERENCE_FILENAME
)

mask_file = os.path.join(
    output_dir,
    MASK_FILENAME
)

test_file = os.path.join(
    output_dir,
    TEST_FILENAME
)

frame_dir = os.path.join(
    output_dir,
    FRAME_DIR_NAME
)

video_file = os.path.join(
    output_dir,
    VIDEO_FILENAME
)


# ============================================================
# 入力内容確認
# ============================================================

print()
print("=" * 60)
print("入力内容の確認")
print("=" * 60)
print()

print(
    f"JPEGディレクトリ:\n"
    f"  {jpeg_dir}"
)

print()

print(
    f"開始画像:\n"
    f"  DSC{START:05d}.jpg"
)

print(
    f"終了画像:\n"
    f"  DSC{END:05d}.jpg"
)

print()

print(
    f"処理枚数:\n"
    f"  {TOTAL}枚"
)

print()

print(
    f"出力先:\n"
    f"  {output_dir}"
)

print()

answer = input(
    "[Enter] → 開始\n"
    "[q]     → 中止\n"
    "> "
).strip().lower()

if answer == "q":
    abort()


# ============================================================
# Phase 1
# 元画像確認
# ============================================================

print()
print("=" * 60)
print("PHASE 1 : 元画像確認")
print("=" * 60)
print()

print(
    f"DSC{START:05d}.jpg"
    f" ～ "
    f"DSC{END:05d}.jpg"
)

print(
    f"合計 {TOTAL}枚"
)

print()
print("ファイル存在確認中...")


for i, n in enumerate(
    range(START, END + 1),
    start=1
):

    filename = os.path.join(
        jpeg_dir,
        f"DSC{n:05d}.jpg"
    )

    if not os.path.exists(filename):

        error(
            f"ファイルがありません:\n"
            f"{filename}"
        )

    if i == 1 or i == TOTAL:

        size = check_image_size(
            filename
        )

        print()
        print(
            f"{filename}"
        )

        print(
            f"サイズ: "
            f"{size[0]} x {size[1]}"
        )

        if size != (WIDTH, HEIGHT):

            error(
                f"画像サイズが想定と異なります。\n\n"
                f"対象: {filename}\n"
                f"実際: {size[0]} x {size[1]}\n"
                f"想定: {WIDTH} x {HEIGHT}"
            )


print()
print(
    f"{TOTAL}枚すべて存在しています。"
)

confirm(
    "PHASE 1 完了\n\n"
    f"{TOTAL}枚の元画像が存在し、"
    "サイズも正常です。"
)


# ============================================================
# Phase 2
# mountain_reference
# ============================================================

print()
print("=" * 60)
print("PHASE 2 : 山の基準画像を作成")
print("=" * 60)
print()

REFERENCE_START = START

REFERENCE_END = min(
    START + REFERENCE_COUNT - 1,
    END
)

reference_files = [
    os.path.join(
        jpeg_dir,
        f"DSC{n:05d}.jpg"
    )
    for n in range(
        REFERENCE_START,
        REFERENCE_END + 1
    )
]

print(
    f"基準画像作成用: "
    f"{len(reference_files)}枚"
)

imgs = []

for i, filename in enumerate(
    reference_files,
    1
):

    print(
        f"{i}/{len(reference_files)}: "
        f"{os.path.basename(filename)}"
    )

    img = Image.open(
        filename
    ).convert("RGB")

    img = img.resize(
        (1326, 1988),
        Image.Resampling.BILINEAR
    )

    imgs.append(
        np.asarray(
            img,
            dtype=np.uint8
        )
    )


stack = np.stack(
    imgs,
    axis=0
)

print()
print("中央値を計算中...")

median = np.median(
    stack,
    axis=0
).astype(np.uint8)

Image.fromarray(
    median,
    "RGB"
).save(
    reference_file,
    quality=95,
    subsampling=0
)

print()
print(
    f"保存: {reference_file}"
)

confirm(
    "PHASE 2 完了\n\n"
    "mountain_reference.jpg を確認してください。\n\n"
    "星などがかなり消え、"
    "山と地上が自然に残っていればOKです。"
)


# ============================================================
# Phase 3
# 山マスク作成
# ============================================================

print()
print("=" * 60)
print("PHASE 3 : 山マスク作成")
print("=" * 60)
print()

img = Image.open(
    reference_file
).convert("L")

a = np.asarray(
    img,
    dtype=np.float32
)

h, w = a.shape

print(
    f"基準画像サイズ: {w} x {h}"
)

blur = img.filter(
    ImageFilter.GaussianBlur(
        radius=12
    )
)

a = np.asarray(
    blur,
    dtype=np.float32
)

y_min = 950
y_max = 1400

diff = np.abs(
    a[5:, :] - a[:-5, :]
)

search = diff[
    y_min:y_max,
    :
]

boundary = (
    np.argmax(
        search,
        axis=0
    )
    + y_min
)

window = 31
half = window // 2

smooth = np.zeros_like(
    boundary
)

for x in range(w):

    x1 = max(
        0,
        x - half
    )

    x2 = min(
        w,
        x + half + 1
    )

    smooth[x] = int(
        np.median(
            boundary[x1:x2]
        )
    )

boundary = smooth

print(
    "推定境界:",
    f"min={boundary.min()}",
    f"max={boundary.max()}",
    f"median={np.median(boundary):.0f}"
)

mask = np.zeros(
    (h, w),
    dtype=np.uint8
)

for x in range(w):

    y = boundary[x]

    mask[
        :y,
        x
    ] = 255


mask_img = Image.fromarray(
    mask,
    "L"
)

mask_img = mask_img.filter(
    ImageFilter.GaussianBlur(
        radius=3
    )
)

mask_img.save(
    mask_file,
    quality=100
)

print()
print(
    f"保存: {mask_file}"
)

confirm(
    "PHASE 3 完了\n\n"
    "mountain_mask_preview.jpg を確認してください。\n\n"
    "白 = 比較明する空\n"
    "黒 = 固定する山・地上\n\n"
    "山の輪郭に沿って"
    "白→黒になっていればOKです。"
)


# ============================================================
# Phase 4
# 5枚テスト
# ============================================================

print()
print("=" * 60)
print("PHASE 4 : 5枚テスト")
print("=" * 60)
print()

TEST_END = min(
    START + TEST_COUNT - 1,
    END
)

test_files = [
    os.path.join(
        jpeg_dir,
        f"DSC{n:05d}.jpg"
    )
    for n in range(
        START,
        TEST_END + 1
    )
]

print("使用画像:")

for f in test_files:
    print(
        f"  {os.path.basename(f)}"
    )


mask_img = Image.open(
    mask_file
).convert("L")

mask_img = mask_img.resize(
    (WIDTH, HEIGHT),
    Image.Resampling.BICUBIC
)

mask = (
    np.asarray(
        mask_img,
        dtype=np.float32
    )
    / 255.0
)

imgs = []

for filename in test_files:

    img = np.asarray(
        Image.open(
            filename
        ).convert("RGB"),
        dtype=np.uint8
    )

    imgs.append(img)


print()
print("5枚を比較明合成中...")

sky = imgs[0].copy()

for img in imgs[1:]:

    sky = np.maximum(
        sky,
        img
    )


ground = imgs[-1]

alpha = mask[..., None]

result = (
    sky.astype(np.float32)
    * alpha
    +
    ground.astype(np.float32)
    * (1.0 - alpha)
)

result = np.clip(
    result,
    0,
    255
).astype(np.uint8)


Image.fromarray(
    result,
    "RGB"
).save(
    test_file,
    quality=100,
    subsampling=0
)

print()
print(
    f"保存: {test_file}"
)

confirm(
    "PHASE 4 完了\n\n"
    "test_5frame_mountain.jpg を確認してください。\n\n"
    "確認ポイント:\n"
    "・星が5枚分比較明になっている\n"
    "・山と地上が自然に固定されている\n"
    "・山の輪郭に不自然なラインがない\n"
    "・全体が不自然に明るくなっていない\n\n"
    "問題なければ全フレーム生成へ進みます。"
)


# ============================================================
# Phase 5
# 連番JPEG生成
# ============================================================

print()
print("=" * 60)
print("PHASE 5 : 累積比較明JPEG生成")
print("=" * 60)
print()

os.makedirs(
    frame_dir,
    exist_ok=True
)

alpha = mask[..., None]

accum = None

for frame_no, n in enumerate(
    range(START, END + 1),
    start=1
):

    filename = os.path.join(
        jpeg_dir,
        f"DSC{n:05d}.jpg"
    )

    print(
        f"[{frame_no:03d}/{TOTAL}] "
        f"DSC{n:05d}.jpg"
    )

    img = np.asarray(
        Image.open(
            filename
        ).convert("RGB"),
        dtype=np.uint8
    )

    if accum is None:

        accum = img.copy()

    else:

        accum = np.maximum(
            accum,
            img
        )

    result = (
        accum.astype(np.float32)
        * alpha
        +
        img.astype(np.float32)
        * (1.0 - alpha)
    )

    result = np.clip(
        result,
        0,
        255
    ).astype(np.uint8)

    output = os.path.join(
        frame_dir,
        f"frame_{frame_no:03d}.jpg"
    )

    Image.fromarray(
        result,
        "RGB"
    ).save(
        output,
        quality=100,
        subsampling=0
    )


print()
print(
    f"{TOTAL}枚の生成完了"
)

confirm(
    "PHASE 5 完了\n\n"
    "以下の3枚を確認してください。\n\n"
    "frame_001.jpg\n"
    f"frame_{TOTAL // 2:03d}.jpg\n"
    f"frame_{TOTAL:03d}.jpg\n\n"
    "星の軌跡が徐々に伸びていればOKです。\n"
    "問題なければ動画を作成します。"
)


# ============================================================
# Phase 6
# FFmpeg動画
# ============================================================

print()
print("=" * 60)
print("PHASE 6 : FFmpegで動画作成")
print("=" * 60)
print()

print(
    "24fps / 1920px幅 / H.264"
)

command = [
    "ffmpeg",
    "-y",
    "-framerate",
    "24",
    "-start_number",
    "1",
    "-i",
    "frame_%03d.jpg",
    "-vf",
    "scale=1920:-2",
    "-c:v",
    "libx264",
    "-crf",
    "18",
    "-preset",
    "medium",
    "-pix_fmt",
    "yuv420p",
    "-movflags",
    "+faststart",
    video_file
]

print()
print(
    "FFmpegを実行します..."
)

subprocess.run(
    command,
    cwd=frame_dir,
    check=True
)

print()
print("=" * 60)
print("完成！")
print("=" * 60)
print()

print(
    f"動画:\n"
    f"  {video_file}"
)

print()

print(
    f"{TOTAL}枚 / 24fps = "
    f"{TOTAL / 24:.2f}秒"
)

print()
