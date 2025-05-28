from sklearn.cluster import DBSCAN
import os
import glob
import numpy as np
from PIL import Image, ImageDraw

# 設定路徑
image_folder = os.path.join("data", "images")
label_folder = os.path.join("runs", "detect", "exp5", "labels")
output_folder = os.path.join("runs", "detect", "exp5", "processed_dbscan")
output_txt_path = os.path.join("runs", "detect", "exp5", "processed_dbscan",  "floor_count_result.txt")

os.makedirs(output_folder, exist_ok=True)

# 搜尋圖片
image_files = glob.glob(os.path.join(image_folder, "*.jpg")) + glob.glob(os.path.join(image_folder, "*.png"))

results = []

for image_path in image_files:
    image_name = os.path.basename(image_path)
    label_path = os.path.join(label_folder, os.path.splitext(image_name)[0] + ".txt")

    if not os.path.exists(label_path):
        continue

    # 讀取 bounding boxes
    boxes = []
    with open(label_path, 'r') as f:
        for line in f:
            parts = list(map(float, line.strip().split()))
            if len(parts) == 5:
                boxes.append(parts)

    if not boxes:
        continue

    # 過濾掉不合理 box（例如太扁）
    filtered_boxes = [b for b in boxes if b[4] > 0.01 and b[4] / b[3] > 0.2]
    if not filtered_boxes:
        continue

    # 使用 y_center 聚類辨識樓層
    y_centers = np.array([[b[2]] for b in filtered_boxes])
    clustering = DBSCAN(eps=0.04, min_samples=1).fit(y_centers)
    labels = clustering.labels_

    # 標記每層樓的群組
    num_floors = len(set(labels))
    merged_boxes = []
    for label in set(labels):
        grouped = [filtered_boxes[i] for i in range(len(filtered_boxes)) if labels[i] == label]
        x_centers = [b[1] for b in grouped]
        y_centers = [b[2] for b in grouped]
        widths = [b[3] for b in grouped]
        heights = [b[4] for b in grouped]

        min_x = min(x - w/2 for x, w in zip(x_centers, widths))
        max_x = max(x + w/2 for x, w in zip(x_centers, widths))
        min_y = min(y - h/2 for y, h in zip(y_centers, heights))
        max_y = max(y + h/2 for y, h in zip(y_centers, heights))

        merged_x_center = (min_x + max_x) / 2
        merged_y_center = (min_y + max_y) / 2
        merged_width = max_x - min_x
        merged_height = max_y - min_y

        merged_boxes.append([0, merged_x_center, merged_y_center, merged_width, merged_height])

    # 畫出合併後的紅框
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    img_width, img_height = img.size

    for box in merged_boxes:
        _, x_center, y_center, width, height = box
        left = int((x_center - width / 2) * img_width)
        top = int((y_center - height / 2) * img_height)
        right = int((x_center + width / 2) * img_width)
        bottom = int((y_center + height / 2) * img_height)
        draw.rectangle([left, top, right, bottom], outline="red", width=3)

    # 儲存圖片與樓層結果
    output_image_path = os.path.join(output_folder, image_name)
    img.save(output_image_path)
    results.append(f"{image_name}: {num_floors} floors")

# 寫入總結果
with open(output_txt_path, 'w') as f:
    f.write("\n".join(results))

output_txt_path