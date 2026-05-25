import multer from "multer";
import path from "path";
import fs from "fs";
import express from "express";
import dotenv from "dotenv";

import {
  predictImageByPath,
  predictText,
  predictMultiByPath,
} from "../services/localModel.js";

dotenv.config();

const router = express.Router();

const uploadDir = "uploads/images/";

if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadDir),
  filename: (req, file, cb) =>
    cb(null, `${Date.now()}${path.extname(file.originalname)}`),
});

const upload = multer({ storage });

router.get("/health", (req, res) => {
  return res.json({
    success: true,
    message: "analyzer router is running",
  });
});

router.post("/image", upload.single("image"), async (req, res) => {
  console.log("[/image] req.file:", req.file);

  if (!req.file || req.file.size === 0) {
    return res.status(400).json({
      success: false,
      message: "Image upload failed (empty file)",
    });
  }

  try {
    const imagepath = req.file.path;
    const parsed = await predictImageByPath(imagepath);

    return res.json({
      success: true,
      message: parsed,
      imagepath,
    });
  } catch (err) {
    console.error("[/image] error:", err);

    return res.status(500).json({
      success: false,
      message: err?.message || "Internal server error",
    });
  }
});

router.post("/text", async (req, res) => {
  try {
    const text = String(
      req.body?.text ?? req.body?.prompt ?? req.body?.message ?? ""
    ).trim();

    console.log("[/text] body:", req.body);
    console.log("[/text] text:", text);

    if (!text) {
      return res.status(400).json({
        success: false,
        message: "text is required",
      });
    }

    const parsed = await predictText(text);

    return res.json({
      success: true,
      message: parsed,
    });
  } catch (err) {
    console.error("[/text] error:", err);

    return res.status(500).json({
      success: false,
      message: err?.message || "Internal server error",
    });
  }
});

router.post("/multi", upload.single("image"), async (req, res) => {
  console.log("[/multi] req.file:", req.file);
  console.log("[/multi] req.body:", req.body);

  if (!req.file || req.file.size === 0) {
    return res.status(400).json({
      success: false,
      message: "Image upload failed (empty file)",
    });
  }

  try {
    const imagepath = req.file.path;
    const userInput = String(
      req.body?.prompt ?? req.body?.text ?? req.body?.message ?? ""
    ).trim();

    const parsed = await predictMultiByPath(imagepath, userInput);

    return res.json({
      success: true,
      message: parsed,
      imagepath,
    });
  } catch (err) {
    console.error("[/multi] error:", err);

    return res.status(500).json({
      success: false,
      message: err?.message || "Internal server error",
    });
  }
});

export default router;