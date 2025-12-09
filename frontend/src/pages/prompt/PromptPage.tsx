import React, { useState, useEffect } from 'react'
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Modal, 
  Form, 
  Input, 
  Select, 
  message,
  Popconfirm,
  Tag
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { promptApi } from '../../services/api'
import type { Prompt } from '../../types'
import dayjs from 'dayjs'

const { Option } = Select

const PromptPage: React.FC = () => {
  const [data, setData] = useState<Prompt[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingPrompt, setEditingPrompt] = useState<Prompt | null>(null)
  const [currentPage, setCurrentPage] = useState<number>(1)
  const [pageSize, setPageSize] = useState<number>(10)
  const [form] = Form.useForm()

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
    },
   
    {
      title: '模型类型',
      dataIndex: 'model_type',
      key: 'model_type',
      render: (modelType: string) => (
        <Tag color={modelType === 'proprietary' ? 'blue' : 'green'}>
          {modelType === 'proprietary' ? '专有模型' : '通用模型'}
        </Tag>
      ),
    },
    {
      title: '系统提示词',
      dataIndex: 'system_prompt',
      key: 'system_prompt',
      render: (systemPrompt: string) => (
        <div
          style={{
            maxWidth: 400,
            overflow: 'hidden',
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical',
            textOverflow: 'ellipsis',
            whiteSpace: 'normal',
          }}
        >
          {systemPrompt || '-'}
        </div>
      ),
    },
    {
      title: '用户提示词',
      dataIndex: 'user_prompt',
      key: 'user_prompt',
      render: (userPrompt: string) => (
        <div
          style={{
            maxWidth: 400,
            overflow: 'hidden',
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical',
            textOverflow: 'ellipsis',
            whiteSpace: 'normal',
          }}
        >
          {userPrompt || '-'}
        </div>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (createdAt: string) => dayjs(createdAt).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Prompt) => (
        <Space>
          <Button 
            type="link" 
            icon={<EditOutlined />} 
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个Prompt吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const fetchData = async () => {
    setLoading(true)
    try {
      const response: any = await promptApi.getList()
      setData(response.data.items)
    } catch (error) {
      message.error('获取数据失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingPrompt(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: Prompt) => {
    setEditingPrompt(record)
    // 转换字段名：后端下划线命名 -> 前端驼峰命名
    form.setFieldsValue({
      title: record.title,
      modelType: record.model_type,
      systemPrompt: record.system_prompt,
      userPrompt: record.user_prompt
    })
    setModalVisible(true)
  }

  const handleDelete = async (id: string) => {
    try {
      await promptApi.delete(id)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      // 转换字段名：前端驼峰命名 -> 后端下划线命名
      const submitData = {
        title: values.title,
        model_type: values.modelType,
        system_prompt: values.systemPrompt,
        user_prompt: values.userPrompt
      }

      if (editingPrompt) {
        await promptApi.update(editingPrompt.id, submitData)
        message.success('更新成功')
      } else {
        await promptApi.create(submitData)
        message.success('创建成功')
      }
      
      setModalVisible(false)
      fetchData()
    } catch (error) {
      message.error(editingPrompt ? '更新失败' : '创建失败')
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  return (
    <div>
      <Card 
        title="Prompt 配置" 
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            新增 Prompt
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={data}
          loading={loading}
          rowKey="id"
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            total: data.length,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total: number) => `共 ${total} 条记录`,
            onChange: (page, newPageSize) => {
              setCurrentPage(page)
              if (newPageSize && newPageSize !== pageSize) {
                setPageSize(newPageSize)
                setCurrentPage(1)
              }
            },
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
        />
      </Card>

      <Modal
        title={editingPrompt ? '编辑 Prompt' : '新增 Prompt'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="title"
            label="标题"
            rules={[{ required: true, message: '请输入标题' }]}
          >
            <Input placeholder="请输入Prompt标题" />
          </Form.Item>

          <Form.Item
            name="modelType"
            label="模型类型"
            rules={[{ required: true, message: '请选择模型类型' }]}
          >
            <Select placeholder="请选择模型类型">
              <Option value="proprietary">专有模型</Option>
              <Option value="general">通用模型</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="systemPrompt"
            label="系统提示词"
            rules={[{ required: false, message: '请输入系统提示词' }]}
          >
            <Input.TextArea 
              placeholder="请输入系统提示词（可选）"
              rows={6}
            />
          </Form.Item>

          <Form.Item
            name="userPrompt"
            label="用户提示词"
            rules={[{ required: false, message: '请输入用户提示词' }]}
          >
            <Input.TextArea 
              placeholder="请输入用户提示词（可选）"
              rows={6}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default PromptPage
