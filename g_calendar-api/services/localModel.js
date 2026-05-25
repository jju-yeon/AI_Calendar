import path from "path";

const AI_MODEL_URL = process.env.AI_MODEL_URL || "http://127.0.0.1:8000";

async function postJson(endpoint, body) {
  const response = await fetch(`${AI_MODEL_URL}${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  const data = await response.json();

  if (!response.ok || !data.success) {
    throw new Error(data.message || "AI model server error");
  }

  return data.message;
}

export async function predictImageByPath(imagePath) {
  return postJson("/predict/image-path", {
    image_path: path.resolve(imagePath),
  });
}

export async function predictText(text) {
  return postJson("/predict/text", {
    text,
  });
}

export async function predictMultiByPath(imagePath, prompt) {
  return postJson("/predict/multi-path", {
    image_path: path.resolve(imagePath),
    prompt: prompt || "",
  });
}