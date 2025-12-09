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
  Tag,
  Select
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { workflowApi } from '../../services/api'
import type { Workflow } from '../../types'
import dayjs from 'dayjs'

const WorkflowPage: React.FC = () => {
  const [data, setData] = useState<Workflow[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingWorkflow, setEditingWorkflow] = useState<Workflow | null>(null)
  const [currentPage, setCurrentPage] = useState<number>(1)
  const [pageSize, setPageSize] = useState<number>(10)
  const [form] = Form.useForm()

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
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const typeMap: { [key: string]: { text: string; color: string } } = {
          proprietary: { text: '专有模型', color: 'blue' },
          'proprietary->general': { text: '专有模型->通用模型', color: 'purple' }
        }
        const typeInfo = typeMap[type] || { text: type, color: 'default' }
        return <Tag color={typeInfo.color}>{typeInfo.text}</Tag>
      },
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
      render: (_: any, record: Workflow) => (
        <Space>
          <Button 
            type="link" 
            icon={<EditOutlined />} 
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个流程吗？"
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
      const response: any = await workflowApi.getList()
      setData(response.data.items)
    } catch (error) {
      message.error('获取数据失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingWorkflow(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: Workflow) => {
    setEditingWorkflow(record)
    // 将 status 转换为 boolean 供 Switch 使用
    form.setFieldsValue({
      ...record,
      status: record.status === 'active'
    })
    setModalVisible(true)
  }

  const handleDelete = async (id: string) => {
    try {
      await workflowApi.delete(id)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      const submitData: any = {
        name: values.name,
        description: values.description,
        type: values.type,
      }

      // 如果是编辑模式，添加 status 字段（将 boolean 转换为 'active'/'inactive'）
      if (editingWorkflow) {
        if (values.status !== undefined) {
          submitData.status = values.status ? 'active' : 'inactive'
        }
        await workflowApi.update(editingWorkflow.id, submitData)
        message.success('更新成功')
      } else {
        await workflowApi.create(submitData)
        message.success('创建成功')
      }
      
      setModalVisible(false)
      fetchData()
    } catch (error) {
      message.error(editingWorkflow ? '更新失败' : '创建失败')
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  return (
    <div>
      <Card 
        title="流程配置" 
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            新增流程
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
        title={editingWorkflow ? '编辑流程' : '新增流程'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={500}
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
            <Input placeholder="请输入流程名称" />
          </Form.Item>

          
          <Form.Item
            name="type"
            label="类型"
            rules={[{ required: true, message: '请选择类型' }]}
          >
            <Select placeholder="请选择模型类型">
              <Select.Option value="proprietary">专有模型</Select.Option>
              <Select.Option value="proprietary->general">专有模型-&gt;通用模型</Select.Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="description"
            label="描述"
            rules={[{ required: true, message: '请输入描述' }]}
          >
            <Input.TextArea placeholder="请输入描述" rows={3} />
          </Form.Item>


          {editingWorkflow && (
            <Form.Item
              name="status"
              label="状态"
              valuePropName="checked"
            >
              <Switch checkedChildren="启用" unCheckedChildren="禁用" />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  )
}

export default WorkflowPage
