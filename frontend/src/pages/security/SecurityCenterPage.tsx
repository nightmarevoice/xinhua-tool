import React, { useState, useEffect } from 'react'
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Modal, 
  Form, 
  Input, 
  message,
  Popconfirm,
  Tag
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, CloseOutlined } from '@ant-design/icons'
import { sensitiveWordApi } from '../../services/api'
import type { SensitiveWordGroup } from '../../types'
import dayjs from 'dayjs'

const SecurityCenterPage: React.FC = () => {
  const [data, setData] = useState<SensitiveWordGroup[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingGroup, setEditingGroup] = useState<SensitiveWordGroup | null>(null)
  const [currentPage, setCurrentPage] = useState<number>(1)
  const [pageSize, setPageSize] = useState<number>(10)
  const [form] = Form.useForm()
  const [words, setWords] = useState<string[]>([''])

  const columns = [
    {
      title: '组名',
      dataIndex: 'name',
      key: 'name',
      width: 200,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: 250,
      render: (description: string) => description || '-',
    },
    {
      title: '敏感词',
      dataIndex: 'words',
      key: 'words',
      render: (words: string[]) => (
        <Space wrap>
          {words && words.length > 0 ? (
            words.map((word, index) => (
              <Tag key={index} color="red">
                {word}
              </Tag>
            ))
          ) : (
            <span>-</span>
          )}
        </Space>
      ),
    },
    {
      title: '敏感词数量',
      dataIndex: 'words',
      key: 'wordCount',
      width: 120,
      align: 'center' as const,
      render: (words: string[]) => words?.length || 0,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (createdAt: string) => dayjs(createdAt).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: SensitiveWordGroup) => (
        <Space>
          <Button 
            type="link" 
            icon={<EditOutlined />} 
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个敏感词组吗？"
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
      const response: any = await sensitiveWordApi.getList()
      setData(response.data.items)
    } catch (error) {
      message.error('获取数据失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingGroup(null)
    setWords([''])
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: SensitiveWordGroup) => {
    setEditingGroup(record)
    form.setFieldsValue({
      name: record.name,
      description: record.description || '',
    })
    setWords(record.words && record.words.length > 0 ? [...record.words] : [''])
    setModalVisible(true)
  }

  const handleDelete = async (id: string) => {
    try {
      await sensitiveWordApi.delete(id)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      // 过滤掉空的敏感词
      const validWords = words.filter(word => word.trim() !== '')
      
      if (validWords.length === 0) {
        message.error('至少需要添加一个敏感词')
        return
      }

      const submitData = {
        name: values.name,
        description: values.description || undefined,
        words: validWords,
      }

      if (editingGroup) {
        await sensitiveWordApi.update(editingGroup.id, submitData)
        message.success('更新成功')
      } else {
        await sensitiveWordApi.create(submitData)
        message.success('创建成功')
      }
      
      setModalVisible(false)
      fetchData()
    } catch (error: any) {
      message.error(editingGroup ? '更新失败' : '创建失败')
    }
  }

  const handleAddWord = () => {
    setWords([...words, ''])
  }

  const handleRemoveWord = (index: number) => {
    const newWords = words.filter((_, i) => i !== index)
    setWords(newWords.length > 0 ? newWords : [''])
  }

  const handleWordChange = (index: number, value: string) => {
    const newWords = [...words]
    newWords[index] = value
    setWords(newWords)
  }

  useEffect(() => {
    fetchData()
  }, [])

  return (
    <div>
      <Card 
        title="安全中心 - 敏感词配置" 
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            新增敏感词组
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
        title={editingGroup ? '编辑敏感词组' : '新增敏感词组'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={700}
        okText="确定"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label="组名"
            rules={[{ required: true, message: '请输入组名' }]}
          >
            <Input placeholder="请输入敏感词组名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea 
              placeholder="请输入描述（可选）"
              rows={3}
            />
          </Form.Item>

          <Form.Item
            label="敏感词列表"
            required
          >
            <div>
              {words.map((word, index) => (
                <div key={index} style={{ marginBottom: 8, display: 'flex', alignItems: 'center' }}>
                  <Input
                    placeholder={`请输入敏感词 ${index + 1}`}
                    value={word}
                    onChange={(e) => handleWordChange(index, e.target.value)}
                    style={{ flex: 1, marginRight: 8 }}
                  />
                  {words.length > 1 && (
                    <Button
                      type="text"
                      danger
                      icon={<CloseOutlined />}
                      onClick={() => handleRemoveWord(index)}
                    />
                  )}
                </div>
              ))}
              <Button
                type="dashed"
                onClick={handleAddWord}
                style={{ width: '100%', marginTop: 8 }}
              >
                <PlusOutlined /> 添加敏感词
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default SecurityCenterPage

