<!--
  @file 设置分组组件
  @description 将相关设置项分组展示
  @component SettingsSection
  @props
    - title: 分组标题
    - description: 分组描述
  @slots
    - default: 设置项内容

  @example
  ```vue
  <template>
    <SettingsSection title="Appearance" description="Customize the look and feel">
      <SettingItem label="Theme" type="select" ... />
    </SettingsSection>
  </template>
  ```
-->

<script setup lang="ts">
/**
 * 组件属性定义
 * @property {string} title - 分组标题
 * @property {string} [description] - 分组描述
 */
interface Props {
  title: string
  description?: string
}

defineProps<Props>()
</script>

<template>
  <section class="settings-section">
    <!-- 分组头部 -->
    <div class="section-header">
      <h3 class="section-title">{{ title }}</h3>
      <p v-if="description" class="section-description">{{ description }}</p>
    </div>
    <!-- 设置项内容插槽 -->
    <div class="section-content">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.settings-section {
  background: var(--surface-color);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  margin-bottom: 1.5rem;
  overflow: hidden;
}

.section-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
  background: var(--background-color);
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.section-description {
  margin-top: 0.25rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

.section-content {
  padding: 0 1.5rem;
}
</style>
