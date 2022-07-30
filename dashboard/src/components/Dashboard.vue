<script setup lang="ts">
import { onMounted, ref } from "vue";
import SelectButton from "./SelectButton.vue";
import Switch from "./Switch.vue";

interface Texture {
  url: string;
  meta?: Record<string, string>;
}

interface User {
  profileName: string;
  profileId: string;
  textures: Record<string, Texture>;
}

enum SkinType {
  SKIN = "skin",
  ELYTRA = "elytra",
}

enum SkinUploadType {
  URL = "url",
  FILE = "file",
}

const userLoading = ref(true);
const user = ref<User | null>(null);
const skinType = ref(SkinType.SKIN);
const skinUploadType = ref<SkinUploadType>(SkinUploadType.URL);
const skinUrl = ref<string | null>(null);
const skinFile = ref<File | null>(null);

function logIn() {
  location.href = "/api/v1/auth/xbox";
}

function logOut() {
  location.href = "/api/v1/auth/logout";
}

async function fetchSkin() {
  const response = await fetch("/api/v1/user/@me");
  const json = await response.json();
  if (response.ok) {
    return json;
  }
  return null;
}

async function uploadSkin(this: HTMLFormElement) {
  const data = new FormData(this);
  const resp = await fetch("/api/v1/user/@me", {
    method: "POST",
    headers: {
      "content-type": "multipart/form-data",
    },
    body: data,
  });
}

function setSkinFile(this: HTMLInputElement) {
  if (this.files?.length) {
    skinFile.value = this.files[0];
  }
}

onMounted(async () => {
  user.value = await fetchSkin();
  userLoading.value = false;
});
</script>

<template>
  <div>
    <header>
      <h1>HD Skins</h1>
    </header>
    <div v-if="userLoading">Loading...</div>
    <div class="content" v-else>
      <button @click="logOut" v-if="user">Log out</button>
      <button @click="logIn" v-else>Log in with Xbox Live</button>
      <div v-if="user">
        <p>Welcome, {{ user.profileName }}!</p>
        <ul>
          <li v-for="(value, key) in user.textures" :key="key">
            Your {{ key }}: {{ value.url }}
            <span v-if="Object.entries(value.meta ?? {}).length">
              ({{ value.meta }})
            </span>
          </li>
        </ul>
        <div>
          Upload type
          <SelectButton
            :options="SkinUploadType"
            v-model:value="skinUploadType"
          />
        </div>
        <form @submit.prevent="uploadSkin">
          <div>
            <span>Skin Type:</span>
            <select name="type" v-model="skinType" required>
              <option>skin</option>
              <option>elytra</option>
            </select>
          </div>
          <Switch :value="skinUploadType">
            <template #url>
              <label>
                Skin URL:
                <input name="file" type="url" v-model="skinUrl" required />
              </label>
            </template>

            <template #file>
              <label>
                Skin File:
                <input name="file" type="file" @change="setSkinFile" required />
              </label>
            </template>
          </Switch>
          <input type="submit" />
        </form>
      </div>
    </div>
  </div>
</template>
