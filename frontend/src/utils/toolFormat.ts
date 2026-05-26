// 格式化工具名称
export function formatToolName(toolName: string): string {
  const nameMap: Record<string, string> = {
    'web_search': '网络搜索',
    'knowledge_search': '知识库搜索',
    'calculator': '计算器',
    'code_runner': '代码执行',
    'code_exec': '代码执行',
    'web_scraper': '网页抓取',
    'load_skill': '加载技能',
    'list_skill_resources': '列出技能资源',
    'read_skill_resource': '读取技能资源',
    'file_write': '写入文件',
    'file_read': '读取文件',
    'file_list': '列出文件',
    'pip_install': '安装Python包',
    'npm_install': '安装NPM包',
  }
  return nameMap[toolName] || toolName
}

// 格式化工具输入（截断过长内容）
export function formatToolInput(input: string): string {
  try {
    const parsed = JSON.parse(input)
    const formatted = JSON.stringify(parsed, null, 2)
    return formatted.length > 300 ? formatted.slice(0, 300) + '...' : formatted
  } catch {
    return input.length > 300 ? input.slice(0, 300) + '...' : input
  }
}
