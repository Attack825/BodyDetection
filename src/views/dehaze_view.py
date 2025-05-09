import os
from pathlib import Path

from flask import Blueprint, jsonify, request
import torch

import src.dehaze.model as net
from src.config import DEHAZE_FOLDER, IMAGE_FOLDER, MODEL_FOLDER
from src.dehaze.dehaze import dehaze_image

dehaze_bp = Blueprint("dehaze", __name__, url_prefix="/")


# 确保去雾后的图片保存目录存在
os.makedirs(DEHAZE_FOLDER, exist_ok=True)

# 初始化模型
dev = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
dehaze_net = net.dehaze_net().to(dev)
dehaze_net.load_state_dict(torch.load(Path(MODEL_FOLDER) / "dehaze.pth", weights_only=True))


@dehaze_bp.route("/dehaze", methods=["POST"])
def dehaze():
    """
    图像去雾接口
    """
    # 获取图片ID
    image_id = request.json.get("image_id")
    if not image_id:
        return jsonify({"error": "No image ID provided"}), 400

    # 在上传目录中查找图片
    for ext in [".jpg", ".jpeg", ".png", ".bmp"]:
        image_name = f"{image_id}{ext}"
        image_path = os.path.join(IMAGE_FOLDER, image_name)
        image_type = os.path.basename(os.path.normpath(DEHAZE_FOLDER))
        if os.path.exists(image_path):
            try:
                # 执行去雾处理
                filename, process_time = dehaze_image(
                    image_path=image_path,
                    dehaze_net=dehaze_net,
                    save_path=DEHAZE_FOLDER,
                )

                return jsonify(
                    {
                        "code": 200,
                        "message": "Dehaze success",
                        "image_name": image_name,
                        "process_time": process_time,
                        "file_path": f"/upload/{image_type}/{filename}",
                    }
                )
            except Exception as e:
                return jsonify({"error": f"Processing failed: {str(e)}"}), 500

    return jsonify({"error": "Image not found"}), 404
