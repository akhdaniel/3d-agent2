<template>
  <div class="container avatar-chat">
    <div class="row justify-content-center">
      <div class="col-sm-12 col-lg-10">
        <div class="card border-0 shadow-sm">
          <div class="card-body">
            <div class="mb-2 avatar-wrapper rounded-4 overflow-hidden">
              <video
                v-if="videoUrl"
                :src="videoUrl"
                controls="0"
                autoplay="1"
                playsinline
                @ended="handleVideoEnded"
                class="w-100 avatar-video"
              />
              <div v-else class="avatar-placeholder w-100 d-flex justify-content-center">
                <img src="/static/idle.png" class="idle-image" alt="Idle avatar" />
              </div>
            </div>

            <div class="row g-2 align-items-stretch">
              <div class="col-sm-12 col-lg-3">
                <input
                  v-model="textQuestion"
                  class="form-control form-control-lg"
                  type="text"
                  placeholder="Type a question..."
                  :disabled="loading"
                  @keyup.enter="sendTypedQuestion"
                />
              </div>
              <div class="col-sm-12 col-lg-3">
                <button
                  class="btn btn-success btn-lg w-100"
                  @click="sendTypedQuestion"
                  :disabled="loading || !textQuestion.trim().length"
                >
                  💬 Send Text
                </button>
              </div>
              <div class="col-sm-12 col-lg-3" v-if="!isRecording">
                <button
                  class="btn btn-primary btn-lg w-100"
                  @click="startRecording"
                  :disabled="loading"
                >
                  🎤 Start Talking
                </button>
              </div>
              <div class="col-sm-12 col-lg-3" v-else>
                <button class="btn btn-danger btn-lg w-100" @click="stopRecording">
                  ⏹ Stop
                </button>
              </div>
            </div>

            <p v-if="loading" class="text-muted mt-3 mb-0">⏳ Processing...</p>
            <p v-if="error" class="text-danger mt-2 mb-0">{{ error }}</p>
          </div>
        </div>
      </div>
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

const API_BASE_URL = "https://agent.nexoira.chat/api"

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
.avatar-chat .card-body {
  padding: 1.5rem;
}

.avatar-wrapper {
  background: #0f172a;
}

.avatar-video {
  max-height: 520px;
  object-fit: cover;
}

.idle-image {
  width: 100%;
  height: auto;
  display: block;
}


</style>
