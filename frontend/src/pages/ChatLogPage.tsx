import React, { useState, useEffect } from 'react'
import { Table, Card, Button, Drawer, Descriptions, Space } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { chatLogApi } from '../services/api'
import ReactJson from 'react-json-view'

interface ChatLog {
    id: number
    call_time: string
    input_params: any
    proprietary_params: any
    proprietary_response: string
    general_params: any
    general_response: string
    duration: number
}

const ChatLogPage: React.FC = () => {
    const [loading, setLoading] = useState(false)
    const [data, setData] = useState<ChatLog[]>([])
    const [total, setTotal] = useState(0)
    const [pagination, setPagination] = useState({
        current: 1,
        pageSize: 10
    })

    const [drawerVisible, setDrawerVisible] = useState(false)
    const [currentLog, setCurrentLog] = useState<ChatLog | null>(null)

    const fetchData = async (page: number, pageSize: number) => {
        setLoading(true)
        try {
            const res = await chatLogApi.getList({
                skip: (page - 1) * pageSize,
                limit: pageSize
            })
            setData(res.items)
            setTotal(res.total)
        } catch (error) {
            console.error('Failed to fetch chat logs:', error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchData(pagination.current, pagination.pageSize)
    }, [pagination])

    const handleTableChange = (newPagination: any) => {
        setPagination(newPagination)
    }

    const showDetails = (record: ChatLog) => {
        setCurrentLog(record)
        setDrawerVisible(true)
    }

    const columns: ColumnsType<ChatLog> = [
        {
            title: 'ID',
            dataIndex: 'id',
            width: 80,
        },
        {
            title: '调用时间',
            dataIndex: 'call_time',
            width: 180,
            render: (text) => new Date(text).toLocaleString()
        },
        {
            title: '耗时(秒)',
            dataIndex: 'duration',
            width: 100,
            render: (val) => val ? val.toFixed(2) : '-'
        },
        {
            title: '操作',
            key: 'action',
            width: 100,
            render: (_, record) => (
                <Button type="link" onClick={() => showDetails(record)}>
                    查看详情
                </Button>
            ),
        },
    ]

    return (
        <div style={{ padding: '24px' }}>
            <Card title="聊天生成记录" bordered={false}>
                <Table
                    columns={columns}
                    dataSource={data}
                    rowKey="id"
                    pagination={{
                        ...pagination,
                        total,
                        showSizeChanger: true,
                        showQuickJumper: true,
                        showTotal: (total) => `共 ${total} 条`
                    }}
                    loading={loading}
                    onChange={handleTableChange}
                />
            </Card>

            <Drawer
                title="日志详情"
                width={800}
                onClose={() => setDrawerVisible(false)}
                open={drawerVisible}
            >
                {currentLog && (
                    <Space direction="vertical" size="large" style={{ width: '100%' }}>
                        <Descriptions title="基本信息" bordered column={1}>
                            <Descriptions.Item label="ID">{currentLog.id}</Descriptions.Item>
                            <Descriptions.Item label="调用时间">{new Date(currentLog.call_time).toLocaleString()}</Descriptions.Item>
                            <Descriptions.Item label="耗时">{currentLog.duration?.toFixed(4)} 秒</Descriptions.Item>
                        </Descriptions>

                        <Card title="输入参数" size="small">
                            <ReactJson src={currentLog.input_params || {}} name={false} displayDataTypes={false} />
                        </Card>

                        {currentLog.proprietary_params && (
                            <Card title="专有模型参数" size="small">
                                <ReactJson src={currentLog.proprietary_params} name={false} displayDataTypes={false} />
                            </Card>
                        )}

                        {currentLog.proprietary_response && (
                            <Card title="专有模型响应" size="small">
                                <div style={{ whiteSpace: 'pre-wrap', maxHeight: '300px', overflow: 'auto' }}>
                                    {currentLog.proprietary_response}
                                </div>
                            </Card>
                        )}

                        {currentLog.general_params && (
                            <Card title="通用模型参数" size="small">
                                <ReactJson src={currentLog.general_params} name={false} displayDataTypes={false} />
                            </Card>
                        )}

                        {currentLog.general_response && (
                            <Card title="通用模型响应" size="small">
                                <div style={{ whiteSpace: 'pre-wrap', maxHeight: '300px', overflow: 'auto' }}>
                                    {currentLog.general_response}
                                </div>
                            </Card>
                        )}
                    </Space>
                )}
            </Drawer>
        </div>
    )
}

export default ChatLogPage
