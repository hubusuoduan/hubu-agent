import request from './request'

/** 配置项信息 */
export interface SettingItem {
  key: string
  type: 'int' | 'float' | 'bool' | 'str'
  group: string
  desc: string
  default_value: any
  current_value: any
  is_modified: boolean
  min?: number
  max?: number
}

/** 按分组的配置 */
export type GroupedSettings = Record<string, SettingItem[]>

/** 获取所有可配置项（按分组） */
export function getSettings() {
  return request.get<{ settings: GroupedSettings }>('/settings')
}

/** 获取所有可配置项（平铺列表） */
export function getSettingsFlat() {
  return request.get<{ settings: SettingItem[] }>('/settings/flat')
}

/** 获取单个配置项 */
export function getSetting(key: string) {
  return request.get<SettingItem>(`/settings/${key}`)
}

/** 更新单个配置项 */
export function updateSetting(key: string, value: any) {
  return request.put<{ success: boolean; data: { key: string; value: any } }>(`/settings/${key}`, { value })
}

/** 批量更新配置项 */
export function batchUpdateSettings(settings: Record<string, any>) {
  return request.put<{ success: boolean; updated: any[]; errors: any[] | null }>('/settings', { settings })
}

/** 重置单个配置项 */
export function resetSetting(key: string) {
  return request.delete<{ success: boolean; key: string }>(`/settings/${key}`)
}

/** 重置所有配置项 */
export function resetAllSettings() {
  return request.post<{ success: boolean; reset_count: number }>('/settings/reset')
}
