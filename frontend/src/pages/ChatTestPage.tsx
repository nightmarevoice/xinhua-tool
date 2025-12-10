import React, { useState, useRef, useEffect } from 'react'
import { 
  Card, 
  Form, 
  Input, 
  Button, 
  Space, 
  message, 
  Typography, 
  Divider,
  Row,
  Col,
  Alert,
  Select
} from 'antd'
import { SendOutlined, ClearOutlined, ThunderboltOutlined, KeyOutlined } from '@ant-design/icons'
import { workflowApi } from '../services/api'
import type { Workflow } from '../types'

const { TextArea } = Input
const { Title, Text } = Typography
const { Option } = Select

const STORAGE_API_KEY = 'workflow_ctl_api_key'

// 文风选项数据
const WRITING_STYLES = [
  {
    "style": "政务通报/汇报体",
    "features": "语言严谨、结构规范、逻辑清晰、用词精准、客观陈述",
    "keywords": ["严谨", "规范", "客观", "书面化"]
  },
  {
    "style": "内部参阅/简报体",
    "features": "观点鲜明、分析深刻、篇幅精炼、问题导向、数据支撑",
    "keywords": ["精炼", "深刻", "分析性", "对策建议"]
  },
  {
    "style": "领导讲话/发言稿体",
    "features": "结构庄重、气势恢宏、号召力强、排比对偶多",
    "keywords": ["庄重", "有力", "鼓动性", "逻辑递进"]
  },
  {
    "style": "权威评论体 (新华时评风)",
    "features": "高屋建瓴、观点鲜明、论证有力、引导舆论",
    "keywords": ["权威", "深刻", "引导性", "大局观"]
  },
  {
    "style": "深度报道/调查体",
    "features": "叙事完整、细节丰富、逻辑严密、背景深远",
    "keywords": ["叙事性", "细节化", "调查感", "穿透力"]
  },
  {
    "style": "标准消息/通稿体",
    "features": "要素齐全（5W1H）、客观中立、倒金字塔结构",
    "keywords": ["客观", "简明", "快速", "标准化"]
  },
  {
    "style": "新闻特写/人物通讯体",
    "features": "情感饱满、描写生动、故事性强、见微知著",
    "keywords": ["生动", "情感", "故事化", "人情味"]
  },
  {
    "style": "宏观经济报道体",
    "features": "(分析) 全局视角、数据驱动、政策敏感、趋势研判",
    "keywords": ["全局观", "数据解读", "产业洞察", "趋势研判"]
  },
  {
    "style": "社会民生报道体",
    "features": "(关怀) 问题导向、政策关联、人文温度、建设性",
    "keywords": ["民生关切", "政策落地", "问题导向", "人文关怀"]
  },
  {
    "style": "红色纪念/党史评论体",
    "features": "(论述) 以史鉴今、价值提炼、思想引领、语言庄重",
    "keywords": ["以史鉴今", "精神传承", "思想引领", "理论深度"]
  },
  {
    "style": "新媒体解读/划重点体",
    "features": "通俗易懂、口语化表达、善用问答和比喻、逻辑清晰",
    "keywords": ["解读", "问答", "通俗化", "一图读懂"]
  },
  {
    "style": "数据新闻/图解文案体",
    "features": "语言精炼、数据驱动、结论清晰、适合可视化呈现",
    "keywords": ["数据驱动", "可视化", "结论导向"]
  },
  {
    "style": "快讯/突发新闻体",
    "features": "极度简短、时效性强、信息核心化、滚动更新",
    "keywords": ["快速", "滚动", "核心信息"]
  },
  {
    "style": "历史讲述/红色故事体",
    "features": "故事性强、代入感强、语言有时代感、连接现实",
    "keywords": ["故事化", "沉浸感", "价值传承"]
  }
]

const ChatTestPage: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [content, setContent] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [apiKey, setApiKey] = useState<string>('')
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [workflowsLoading, setWorkflowsLoading] = useState(false)
  const abortControllerRef = useRef<AbortController | null>(null)
  const contentRef = useRef<HTMLDivElement>(null)

  // 从 localStorage 加载 API key
  useEffect(() => {
    const savedApiKey = localStorage.getItem(STORAGE_API_KEY)
    if (savedApiKey) {
      setApiKey(savedApiKey)
    } else {
      // 默认值
      setApiKey('ak_5i_PjMh5bDSjWZN1xLnsLFj2NTV_G3DSwNy1Q01WNgE')
    }
  }, [])

  // 获取启用的 workflows
  const fetchWorkflows = async () => {
    if (!apiKey || !apiKey.trim()) {
      return
    }

    setWorkflowsLoading(true)
    try {
      // 使用 workflowApi.getList 获取流程列表
      // 注意：如果需要过滤 status=active，可能需要后端接口支持该参数
      // 拦截器会自动从 localStorage 的 'workflow_ctl_api_key' 读取 API Key
      const result: any = await workflowApi.getList({ 
        page: 1, 
        page_size: 100,
        // @ts-ignore - status 参数可能不在类型定义中，但后端可能支持
        status: 'active'
      } as any)
      if (result.data && result.data.items) {
        setWorkflows(result.data.items)
      }
    } catch (error: any) {
      console.error('获取 workflows 失败:', error)
      message.error(`获取流程列表失败: ${error.message}`)
    } finally {
      setWorkflowsLoading(false)
    }
  }

  // 当 API Key 变化时，重新获取 workflows
  useEffect(() => {
    if (apiKey && apiKey.trim()) {
      fetchWorkflows()
    }
  }, [apiKey])

  // 自动滚动到底部
  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight
    }
  }, [content])

  const handleSubmit = async (values: any) => {
    if (isStreaming) {
      message.warning('正在流式输出中，请等待完成或点击停止')
      return
    }

    setLoading(true)
    setIsStreaming(true)
    setContent('')
    
    // 创建 AbortController 用于取消请求
    abortControllerRef.current = new AbortController()

    try {
      // 处理用户消息：如果选择了文风，则拼接文风特点
      let userMessage = values.user_message || ''
      if (values.writing_style) {
        const selectedStyle = WRITING_STYLES.find(s => s.style === values.writing_style)
        if (selectedStyle) {
          userMessage = `${userMessage},| 文风: ${values.writing_style} | 核心特点：${selectedStyle.features}`
        }
      }

      const requestData: any = {
        user_message: userMessage,
      }

      // 添加 workflowId（必填）
      if (values.workflowId) {
        requestData.workflowId = values.workflowId
      }

      // 添加可选参数
      if (values.model) {
        requestData.model = values.model
      }
      if (values.llm_provider_id) {
        requestData.llm_provider_id = parseInt(values.llm_provider_id)
      }
      if (values.prompt_id) {
        requestData.prompt_id = parseInt(values.prompt_id)
      }
      if (values.workflow_id) {
        requestData.workflow_id = parseInt(values.workflow_id)
      }
      if (values.temperature !== undefined) {
        requestData.temperature = parseFloat(values.temperature)
      }
      if (values.max_tokens) {
        requestData.max_tokens = parseInt(values.max_tokens)
      }

      // 验证 API Key
      if (!apiKey || !apiKey.trim()) {
        message.error('请先设置 API Key')
        return
      }
      
      // 直接调用流式接口
      const response = await fetch('http://localhost:8889/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': apiKey.trim()
        },
        body: JSON.stringify(requestData),
        signal: abortControllerRef.current.signal
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`请求失败: ${response.status} ${errorText}`)
      }

      // 读取流式响应
      const reader = response.body?.getReader()
      const decoder = new TextDecoder('utf-8')
      
      if (!reader) {
        throw new Error('无法读取响应流')
      }

      let buffer = ''
      let fullContent = ''

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          break
        }

        // 解码数据块
        buffer += decoder.decode(value, { stream: true })
        
        // 按行处理
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // 保留最后一个不完整的行

        for (const line of lines) {
          if (line.trim()) {
            // 处理 SSE 格式：data: {...}
            if (line.startsWith('data: ')) {
              const dataStr = line.substring(6).trim()
              
              if (dataStr === '[DONE]') {
                setIsStreaming(false)
                setLoading(false)
                message.success('流式输出完成')
                return
              }

              try {
                const data = JSON.parse(dataStr)
                const eventType = data.type || ''

                if (eventType === 'content') {
                  const chunk = data.content || ''
                  if (chunk) {
                    fullContent += chunk
                    setContent(fullContent)
                  }
                } else if (eventType === 'done') {
                  setIsStreaming(false)
                  setLoading(false)
                  message.success('流式输出完成')
                  return
                } else if (eventType === 'error') {
                  setIsStreaming(false)
                  setLoading(false)
                  message.error(`错误: ${data.message || '未知错误'}`)
                  return
                } else if (eventType === 'start') {
                  // 开始事件，可以显示提示信息
                  console.log('开始接收流式数据...')
                }
              } catch (e) {
                // 忽略 JSON 解析错误
                console.warn('解析 SSE 数据失败:', dataStr, e)
              }
            }
          }
        }
      }

      setIsStreaming(false)
      setLoading(false)
      message.success('流式输出完成')
    } catch (error: any) {
      setIsStreaming(false)
      setLoading(false)
      
      if (error.name === 'AbortError') {
        message.info('请求已取消')
      } else {
        message.error(`请求失败: ${error.message}`)
        console.error('流式请求错误:', error)
      }
    }
  }

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    setIsStreaming(false)
    setLoading(false)
    message.info('已停止流式输出')
  }

  const handleClear = () => {
    setContent('')
    form.resetFields()
  }

  const handleApiKeyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newApiKey = e.target.value
    setApiKey(newApiKey)
    // 保存到 localStorage
    if (newApiKey.trim()) {
      localStorage.setItem(STORAGE_API_KEY, newApiKey)
    } else {
      localStorage.removeItem(STORAGE_API_KEY)
    }
  }

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>
        <ThunderboltOutlined /> 智能生成新闻
      </Title>
      
      <Divider />

      <Alert
        message="API Key 配置"
        description={
          <Space direction="vertical" style={{ width: '100%', marginTop: '8px' }}>
            <Input
              prefix={<KeyOutlined />}
              placeholder="请输入 API Key"
              value={apiKey}
              onChange={handleApiKeyChange}
              type="password"
              style={{ maxWidth: '600px' }}
            />
            <Text type="secondary" style={{ fontSize: '12px' }}>
              API Key 会自动保存到本地，用于调用流式聊天接口
            </Text>
          </Space>
        }
        type="info"
        showIcon
        style={{ marginBottom: '24px' }}
      />

      <Row gutter={16}>
        <Col span={12}>
          <Card title="请求参数" size="small">
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSubmit}
              initialValues={{
                temperature: 0.7,
                max_tokens: 4096
              }}
            >
              <Form.Item
                name="user_message"
                label="用户消息"
                rules={[{ required: true, message: '请输入用户消息' }]}
              >
                <TextArea 
                  rows={4} 
                  placeholder="请输入要发送的消息..."
                />
              </Form.Item>

              <Form.Item
                name="writing_style"
                label="选择文风"
              >
                <Select
                  placeholder="请选择文风（可选）"
                  allowClear
                  showSearch
                  optionFilterProp="children"
                >
                  {WRITING_STYLES.map((item) => (
                    <Option key={item.style} value={item.style}>
                      {item.style}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
              
              <Form.Item
                name="workflowId"
                label="选择流程"
                rules={[{ required: true, message: '请选择流程' }]}
              >
                <Select
                  placeholder="请选择流程"
                  showSearch
                  loading={workflowsLoading}
                  filterOption={(input, option) => {
                    const label = option?.children?.toString() || ''
                    return label.toLowerCase().includes(input.toLowerCase())
                  }}
                >
                  {workflows.map((workflow) => (
                    <Option key={workflow.id} value={workflow.id}>
                      {workflow.name} 
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item>
                <Space>
                  <Button 
                    type="primary" 
                    htmlType="submit" 
                    icon={<SendOutlined />}
                    loading={loading}
                    disabled={isStreaming}
                  >
                    {isStreaming ? '流式输出中...' : '发送请求'}
                  </Button>
                  {isStreaming && (
                    <Button 
                      danger 
                      onClick={handleStop}
                    >
                      停止
                    </Button>
                  )}
                  <Button 
                    icon={<ClearOutlined />}
                    onClick={handleClear}
                    disabled={isStreaming}
                  >
                    清空
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col span={12}>
          <Card 
            title="流式输出内容" 
            size="small"
            extra={
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {content.length > 0 && `字符数: ${content.length}`}
              </Text>
            }
          >
            <div
              ref={contentRef}
              style={{
                minHeight: '400px',
                maxHeight: '600px',
                overflowY: 'auto',
                padding: '12px',
                backgroundColor: '#f5f5f5',
                borderRadius: '4px',
                fontFamily: 'monospace',
                fontSize: '14px',
                lineHeight: '1.6',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word'
              }}
            >
              {content || (
                <Text type="secondary" style={{ fontStyle: 'italic' }}>
                  等待发送请求，响应内容将实时显示在这里...
                </Text>
              )}
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default ChatTestPage



