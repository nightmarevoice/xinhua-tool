import React, { useState, useEffect } from 'react'
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  message,
  Popconfirm,
  Tag
} from 'antd'
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined
} from '@ant-design/icons'
import { llmProviderApi } from '../../services/api'
import type { LLMProvider as LLMProviderType } from '../../types'
import dayjs from 'dayjs'
import ProviderModal from './ProviderModal'

// 使用从 types 导入的类型

interface ProviderType {
  value: string;
  label: string;
  description: string;
}


const ModelPage: React.FC = () => {
  const [data, setData] = useState<LLMProviderType[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingProvider, setEditingProvider] = useState<LLMProviderType | null>(null)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [currentPage, setCurrentPage] = useState<number>(1)
  const [pageSize, setPageSize] = useState<number>(10)
  
  // ProviderModal需要的props
  const [providerTypes] = useState<ProviderType[]>([
    { value: 'openai', label: 'OpenAI', description: 'OpenAI API服务' },
    { value: 'azure', label: 'Azure OpenAI', description: 'Azure OpenAI服务' },
    { value: 'anthropic', label: 'Anthropic', description: 'Claude API服务' },
    { value: 'google', label: 'Google', description: 'Google AI服务' },
    { value: 'custom', label: '自定义', description: '自定义API服务' }
  ])
  

  const columns = [
    {
      title: '模型名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <div style={{ fontWeight: 'bold' }}>{name}</div>
      ),
    },
    {
      title: '服务商',
      dataIndex: 'provider',
      key: 'provider',
      render: (provider: string) => (
        <Tag color={provider === 'openai' ? 'blue' : provider === 'azure' ? 'purple' : 'green'}>
          {provider.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: '模型类别',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => (
        <Tag color={category === 'general' ? 'blue' : 'orange'}>
          {category === 'general' ? '通用模型' : '专有模型'}
        </Tag>
      ),
    },
    {
      title: '默认模型',
      dataIndex: 'default_model_name',
      key: 'default_model_name',
      render: (modelName: string) => (
        <div style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {modelName}
        </div>
      ),
    },
    {
      title: '视觉模型',
      dataIndex: 'default_vision_model',
      key: 'default_vision_model',
      render: (visionModel: string) => (
        <div style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {visionModel || '-'}
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
      render: (_: any, record: LLMProviderType) => (
        <Space>
          <Button 
            type="link" 
            icon={<EditOutlined />} 
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个Provider吗？"
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
      const response: any = await llmProviderApi.getList()
      // response 已经是 PaginatedData 结构，直接访问 items
      setData(response.data?.items || [])
    } catch (error) {
      console.error('获取数据失败:', error)
      message.error('获取数据失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingProvider(null)
    setModalMode('create')
    setModalVisible(true)
  }

  const handleEdit = (record: LLMProviderType) => {
    setEditingProvider(record)
    setModalMode('edit')
    setModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await llmProviderApi.delete(id)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      message.error('删除失败')
    }
  }

  // ProviderModal的保存处理
  const handleProviderSave = async (provider: LLMProviderType) => {
    try {
      if (editingProvider) {
        await llmProviderApi.update(editingProvider.id, provider)
        message.success('更新成功')
      } else {
        await llmProviderApi.create(provider)
        message.success('创建成功')
      }
      
      setModalVisible(false)
      fetchData()
    } catch (error) {
      message.error('操作失败')
      throw error
    }
  }

  const handleModalClose = () => {
    setModalVisible(false)
    setEditingProvider(null)
  }

  useEffect(() => {
    fetchData()
  }, [])

  return (
    <div>
      <Card 
        title="模型参数配置" 
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            新增模型
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

      <ProviderModal
        isOpen={modalVisible}
        mode={modalMode}
        provider={editingProvider as any}
        onClose={handleModalClose}
        onSave={handleProviderSave as any}
        providerTypes={providerTypes}
      />
    </div>
  )
}

export default ModelPage
