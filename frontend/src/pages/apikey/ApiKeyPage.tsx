import React, { useState, useEffect } from 'react'
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Modal, 
  Form, 
  Input, 
  Switch, 
  message,
  Popconfirm,
  Tag
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, CopyOutlined } from '@ant-design/icons'
import { apiKeyApi } from '../../services/api'
import type { ApiKey } from '../../types'
import dayjs from 'dayjs'

const ApiKeyPage: React.FC = () => {
  const [data, setData] = useState<ApiKey[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingKey, setEditingKey] = useState<ApiKey | null>(null)
  const [createdKey, setCreatedKey] = useState<string | null>(null)
  const [keyModalVisible, setKeyModalVisible] = useState(false)
  const [currentPage, setCurrentPage] = useState<number>(1)
  const [pageSize, setPageSize] = useState<number>(10)
  const [form] = Form.useForm()

  // 兼容的复制到剪贴板函数
  const copyToClipboard = async (text: string) => {
    try {
      // 优先使用现代的 Clipboard API
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text)
        message.success('已复制到剪贴板')
        return
      }
      
      // Fallback: 使用传统的 document.execCommand 方法
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      textArea.style.top = '-999999px'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      
      try {
        const successful = document.execCommand('copy')
        if (successful) {
          message.success('已复制到剪贴板')
        } else {
          throw new Error('复制失败')
        }
      } finally {
        document.body.removeChild(textArea)
      }
    } catch (error) {
      console.error('复制失败:', error)
      message.error('复制失败，请手动选择文本复制')
    }
  }

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: 'API Key',
      dataIndex: 'key',
      key: 'key',
      render: (key: string) => (
        <div 
          style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            cursor: 'pointer',
            padding: '4px 8px',
            borderRadius: '4px',
            transition: 'background-color 0.2s'
          }}
          onClick={() => copyToClipboard(key)}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#f5f5f5'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent'
          }}
          title="点击复制完整API Key"
        >
          <span style={{ fontFamily: 'monospace' }}>
            {key.substring(0, 8)}...{key.substring(key.length - 8)}
          </span>
          <CopyOutlined style={{ color: '#1890ff', fontSize: '12px' }} />
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status === 'active' ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (created_at: string) => created_at ? dayjs(created_at).format('YYYY-MM-DD HH:mm:ss') : '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ApiKey) => (
        <Space>
          <Button 
            type="link" 
            icon={<EditOutlined />} 
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个API Key吗？"
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
    try{
      const response = await apiKeyApi.getList() as any
      setData(response.data?.items || []);
    } catch (error) {
      console.error('获取数据失败:', error)
      message.error('获取数据失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingKey(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: ApiKey) => {
    setEditingKey(record)
    form.setFieldsValue({
      ...record,
    })
    setModalVisible(true)
  }

  const handleDelete = async (id: string) => {
    try {
      await apiKeyApi.delete(id)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      if (editingKey) {
        await apiKeyApi.update(editingKey.id, values)
        message.success('更新成功')
        setModalVisible(false)
        fetchData()
      } else {
        const response = await apiKeyApi.create(values) as any
        setCreatedKey(response.data.key)
        setKeyModalVisible(true)
        setModalVisible(false)
        fetchData()
      }
    } catch (error) {
      message.error(editingKey ? '更新失败' : '创建失败')
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  return (
    <div>
      <Card 
        title="API Key 管理" 
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            新增 API Key
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
        title={editingKey ? '编辑 API Key' : '新增 API Key'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入名称' }]}
          >
            <Input placeholder="请输入API Key名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
            rules={[{ required: true, message: '请输入描述' }]}
          >
            <Input.TextArea placeholder="请输入描述" rows={3} />
          </Form.Item>

          {editingKey && (
            <Form.Item
              name="status"
              label="状态"
              getValueProps={value => ({ checked: value === "active" })}
              getValueFromEvent={checked => (checked ? "active" : "disabled")}
              valuePropName={undefined /* 防止form默认处理checked */}
            >
              <Switch checkedChildren="启用" unCheckedChildren="禁用" />
            </Form.Item>
          )}
        </Form>
      </Modal>

      <Modal
        title="API Key 创建成功"
        open={keyModalVisible}
        onCancel={() => setKeyModalVisible(false)}
        footer={[
          <Button key="copy" type="primary" onClick={() => copyToClipboard(createdKey || '')}>
            复制
          </Button>,
          <Button key="close" onClick={() => setKeyModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={600}
      >
        <div style={{ marginBottom: 16 }}>
          <p>您的API Key已创建成功，请妥善保存：</p>
          <div style={{ 
            background: '#f5f5f5', 
            padding: '12px', 
            borderRadius: '4px',
            fontFamily: 'monospace',
            wordBreak: 'break-all',
            fontSize: '14px'
          }}>
            {createdKey}
          </div>
         
        </div>
      </Modal>
    </div>
  )
}

export default ApiKeyPage
