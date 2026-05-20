<template>
  <div id="app">
    <nav v-if="showSidebar" class="app-sidebar">
      <div class="sidebar-logo">Hubu Agent</div>
      <router-link to="/" class="nav-item" active-class="active">
        <el-icon><ChatDotRound /></el-icon>
        <span>对话</span>
      </router-link>
      <router-link to="/knowledge" class="nav-item" active-class="active">
        <el-icon><FolderOpened /></el-icon>
        <span>知识库</span>
      </router-link>
    </nav>
    <div class="app-content">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { ChatDotRound, FolderOpened } from '@element-plus/icons-vue'

const route = useRoute()

const showSidebar = computed(() => {
  return route.meta.requiresAuth !== false
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Microsoft YaHei', Arial, sans-serif;
  height: 100vh;
  width: 100vw;
  display: flex;
}

.app-sidebar {
  width: 220px;
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

.sidebar-logo {
  padding: 24px 20px;
  font-size: 20px;
  font-weight: bold;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 24px;
  text-decoration: none;
  color: rgba(255, 255, 255, 0.8);
  font-size: 15px;
  font-weight: 500;
  transition: all 0.2s;
}

.nav-item:hover {
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.nav-item.active {
  color: white;
  background: rgba(255, 255, 255, 0.2);
  border-left: 4px solid white;
}

.app-content {
  flex: 1;
  overflow: hidden;
  background-color: #f5f7fa;
}
</style>
