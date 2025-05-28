import os
import glob
from PIL import Image, ImageDraw

# 設定資料夾
image_folder = os.path.join("data", "images")
label_folder = os.path.join("runs", "detect", "exp5", "labels")
output_folder = os.path.join("runs", "detect", "exp5", "processed")

# 建立輸出資料夾
os.makedirs(output_folder, exist_ok=True)

# 讀取所有圖片
image_files = glob.glob(os.path.join(image_folder, "*.jpg")) + glob.glob(os.path.join(image_folder, "*.png"))

if not image_files:
    print("❌ 找不到任何圖片")
    exit()

# 處理每一張圖片
for image_path in image_files:
    image_name = os.path.basename(image_path)
    label_path = os.path.join(label_folder, os.path.splitext(image_name)[0] + ".txt")

    if not os.path.exists(label_path):
        print(f"⚠️ 找不到對應的 label 檔案：{label_path}")
        continue

    # 讀取 label
    bounding_boxes = []
    with open(label_path, 'r') as file:
        for line in file:
            data = list(map(float, line.split()))
            bounding_boxes.append(data)

    if not bounding_boxes:
        print(f"⚠️ 標註為空：{label_path}")
        continue

    # 樓層合併邏輯
    y_threshold = 0.01
    bounding_boxes = sorted(bounding_boxes, key=lambda x: x[2])
    merged_boxes = []
    current_floor = []

    for box in bounding_boxes:
        if not current_floor:
            current_floor.append(box)
        elif abs(box[2] - current_floor[-1][2]) < y_threshold:
            current_floor.append(box)
        else:
            x_centers = [b[1] for b in current_floor]
            y_centers = [b[2] for b in current_floor]
            widths = [b[3] for b in current_floor]
            heights = [b[4] for b in current_floor]

            min_x = min(x - w/2 for x, w in zip(x_centers, widths))
            max_x = max(x + w/2 for x, w in zip(x_centers, widths))
            min_y = min(y - h/2 for y, h in zip(y_centers, heights))
            max_y = max(y + h/2 for y, h in zip(y_centers, heights))

            merged_boxes.append([
                0,
                (min_x + max_x) / 2,
                (min_y + max_y) / 2,
                max_x - min_x,
                max_y - min_y
            ])
            current_floor = [box]

    # 處理最後一層
    if current_floor:
        x_centers = [b[1] for b in current_floor]
        y_centers = [b[2] for b in current_floor]
        widths = [b[3] for b in current_floor]
        heights = [b[4] for b in current_floor]

        min_x = min(x - w/2 for x, w in zip(x_centers, widths))
        max_x = max(x + w/2 for x, w in zip(x_centers, widths))
        min_y = min(y - h/2 for y, h in zip(y_centers, heights))
        max_y = max(y + h/2 for y, h in zip(y_centers, heights))

        merged_boxes.append([
            0,
            (min_x + max_x) / 2,
            (min_y + max_y) / 2,
            max_x - min_x,
            max_y - min_y
        ])

    # 開啟圖片畫框
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    img_width, img_height = img.size

    for box in merged_boxes:
        class_id, x_center, y_center, width, height = box
        left = int((x_center - width / 2) * img_width)
        top = int((y_center - height / 2) * img_height)
        right = int((x_center + width / 2) * img_width)
        bottom = int((y_center + height / 2) * img_height)
        draw.rectangle([left, top, right, bottom], outline="red", width=3)

    # 儲存圖片
    save_path = os.path.join(output_folder, image_name)
    img.save(save_path)
    print(f"✅ 已儲存：{save_path}")
