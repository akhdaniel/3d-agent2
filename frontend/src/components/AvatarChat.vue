<template>
  <div class="chat-container">

    <div class="avatar-wrapper">
      <video
        v-if="videoUrl"
        :src="videoUrl"
        controls="0"
        autoplay="1"
        playsinline
        @ended="handleVideoEnded"
        class="avatar-video"
      />
      <div v-else class="avatar-placeholder">
        <img src="/static/idle.png" class="avatar-video" />
        <!-- <video
          :src="idleVideoSrc"
          controls="0"
          autoplay="1"
          loop
          muted
          playsinline
          class="avatar-video"
        /> -->
        
      </div>
    </div>

    <div class="controls">
      <input
        v-model="textQuestion"
        class="text-question-input"
        type="text"
        placeholder="Type a question..."
        :disabled="loading"
        @keyup.enter="sendTypedQuestion"
      />
      <button
        class="btn send-text"
        @click="sendTypedQuestion"
        :disabled="loading || !textQuestion.trim().length"
      >
        💬 Send Text
      </button>
      <button v-if="!isRecording" @click="startRecording" class="btn start" :disabled="loading">
        🎤 Start Talking
      </button>
      <button v-if="isRecording" @click="stopRecording" class="btn stop">
        ⏹ Stop
      </button>

      <p v-if="loading" class="loading">⏳ Processing...</p>
      <p v-if="error" class="error">{{ error }}</p>
    </div>

  </div>
</template>

<script setup>
import { ref } from "vue";

const isRecording = ref(false);
const loading = ref(false);
const error = ref("");
const videoUrl = ref("");
const textQuestion = ref("");
const idleVideoSrc = new URL("../../static/idle.mp4", import.meta.url).href;
// const fallbackBase =
//   typeof window !== "undefined" &&
//   (window.location.hostname === "localhost" ||
//     window.location.hostname === "127.0.0.1")
//     ? "http://localhost:28000"
//     : typeof window !== "undefined"
//     ? window.location.origin
//     : "http://localhost:28000";
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL
).replace(/\/$/, "");

let chunks = [];
let mediaRecorder = null;

async function startRecording() {
  error.value = "";
  videoUrl.value = "";

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    chunks = [];
    mediaRecorder = new MediaRecorder(stream, {
      mimeType: "audio/webm"   // Native, reliable
    });

    mediaRecorder.ondataavailable = e => {
      if (e.data.size > 0) chunks.push(e.data);
    };

    mediaRecorder.start();
    isRecording.value = true;

  } catch (e) {
    error.value = "Microphone blocked or unsupported.";
    console.error("Mic error:", e);
  }
}

async function stopRecording() {
  if (!mediaRecorder) return;

  isRecording.value = false;
  loading.value = true;

  return new Promise(resolve => {
    mediaRecorder.onstop = async () => {
      const blob = new Blob(chunks, { type: "audio/webm" });

      if (blob.size === 0) {
        error.value = "Audio recorded was empty — please check your microphone.";
        loading.value = false;
        return;
      }

      const form = new FormData();
      form.append("audio", blob, "audio.webm");

      try {
        const res = await fetch(`${API_BASE_URL}/talk`, {
          method: "POST",
          body: form,
        });

        const data = await res.json();
        videoUrl.value = data.video_url;
      } catch (err) {
        console.error(err);
        error.value = "Server error generating response.";
      }

      loading.value = false;
      resolve();
    };

    mediaRecorder.stop();
  });
}

async function sendTypedQuestion() {
  if (!textQuestion.value.trim()) {
    error.value = "Please type a question before sending.";
    return;
  }

  error.value = "";
  videoUrl.value = "";
  loading.value = true;

  const form = new FormData();
  form.append("text", textQuestion.value.trim());

  try {
    const res = await fetch(`${API_BASE_URL}/talk`, {
      method: "POST",
      body: form,
    });

    const data = await res.json();
    if (!res.ok) {
      const serverMessage =
        data?.detail?.message ||
        data?.detail ||
        data?.message ||
        JSON.stringify(data);
      throw new Error(serverMessage || "Server returned an error.");
    }

    if (data.video_url) {
      videoUrl.value = data.video_url;
      textQuestion.value = "";
    } else {
      throw new Error("Invalid response from server.");
    }
  } catch (err) {
    console.error(err);
    const details =
      err instanceof Error ? err.message : JSON.stringify(err, null, 2);
    error.value = `Server error generating response from text: ${details}`;
  } finally {
    loading.value = false;
  }
}

function handleVideoEnded() {
  videoUrl.value = "";
}

</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 100%;
}

.controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
}

.text-question-input {
  flex: 1;
  min-width: 200px;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  border: 1px solid #ccc;
  font-size: 1rem;
}

.btn {
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.95rem;
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.start {
  background-color: #2d8bff;
  color: #fff;
}

.stop {
  background-color: #ff4949;
  color: #fff;
}

.send-text {
  background-color: #4caf50;
  color: #fff;
}

.loading {
  color: #555;
}

.error {
  color: #ff4949;
}
.avatar-video{
  width: 60%;
  padding: 20px;
}
</style>
