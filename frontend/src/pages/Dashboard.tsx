import React, { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Spin, message, Table, Button, Space, InputNumber, Tooltip } from 'antd'
import { Column, Line } from '@ant-design/charts'
import { KeyOutlined, ApartmentOutlined, FileTextOutlined, SettingOutlined, FileSearchOutlined, ReloadOutlined } from '@ant-design/icons'
import { apiKeyApi, workflowApi, promptApi, modelParameterApi, logApi } from '../services/api'
import dayjs from 'dayjs'

interface Stats {
  apiKeys: number
  workflows: number
  prompts: number
  modelParameters: number
  logs: number
}

interface LogLine {
  key: number
  lineNumber: number
  Time?: string
  Status?: number
  Model?: string
  Tokens?: number | null
  content?: string
}

interface ChartData {
  date: string
  count: number
  tokens: number
}

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<Stats>({
    apiKeys: 0,
    workflows: 0,
    prompts: 0,
    modelParameters: 0,
    logs: 0,
  })
  const [logLoading, setLogLoading] = useState(false)
  const [logData, setLogData] = useState<LogLine[]>([])
  const [logLines, setLogLines] = useState<number>(50)
  const [currentPage, setCurrentPage] = useState<number>(1)
  const [pageSize, setPageSize] = useState<number>(20)
  const [chartData, setChartData] = useState<ChartData[]>([])
  const [chartLoading, setChartLoading] = useState(false)

  useEffect(() => {
    fetchStats()
    fetchLogs()
    fetchChartData()
  }, [])

  const fetchStats = async () => {
    setLoading(true)
    try {
      const [apiKeysRes, workflowsRes, promptsRes, modelParametersRes, logsRes] = await Promise.all([
        apiKeyApi.getStats().catch(() => ({ data: { total_count: 0 } })),
        workflowApi.getStats().catch(() => ({ data: { total_count: 0 } })),
        promptApi.getStats().catch(() => ({ data: { total_count: 0 } })),
        modelParameterApi.getStats().catch(() => ({ data: { total_count: 0 } })),
        logApi.getStats().catch(() => ({ data: { total_count: 0 } })),
      ])

      setStats({
        apiKeys: (apiKeysRes as any)?.data?.total_count || 0,
        workflows: (workflowsRes as any)?.data?.total_count || 0,
        prompts: (promptsRes as any)?.data?.total_count || 0,
        modelParameters: (modelParametersRes as any)?.data?.total_count || 0,
        logs: (logsRes as any)?.data?.total_count || 0,
      })
    } catch (error) {
      console.error('获取统计数据失败:', error)
      message.error('获取统计数据失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchLogs = async (lines?: number) => {
    setLogLoading(true)
    try {
      const response = await logApi.getLogs(lines || logLines)
      const content = (response.data as any)?.content || []
      
      // 处理数组格式的日志数据
      let logArray: any[] = []
      
      // 如果 content 是数组，直接使用
      if (Array.isArray(content)) {
        logArray = content
      } 
      // 如果 content 是字符串，尝试解析为 JSON 数组
      else if (typeof content === 'string') {
        try {
          logArray = JSON.parse(content)
          if (!Array.isArray(logArray)) {
            logArray = []
          }
        } catch (e) {
          // 如果解析失败，按行分割作为后备方案
          const logLinesArray = content.split('\n').filter((line: string) => line.trim())
          logArray = logLinesArray.map((line: string) => {
            try {
              return JSON.parse(line.trim())
            } catch {
              return { content: line.trim() }
            }
          })
        }
      }
      
      // 将日志转换为表格数据，最新的日志在顶部
      const formattedLogs: LogLine[] = logArray
        .reverse()
        .map((item: any, index: number) => ({
          key: index,
          lineNumber: index + 1,
          Time: item.Time || item.time || '',
          Status: item.Status !== undefined ? item.Status : (item.status !== undefined ? item.status : null),
          Model: item.Model || item.model || '',
          Tokens: item.Tokens !== undefined ? item.Tokens : (item.tokens !== undefined ? item.tokens : null),
          content: item.content || JSON.stringify(item),
        }))
      
      setLogData(formattedLogs)
    } catch (error) {
      console.error('获取日志失败:', error)
      message.error('获取日志失败')
    } finally {
      setLogLoading(false)
    }
  }

  const handleLogLinesChange = (value: number | null) => {
    if (value && value >= 1 && value <= 1000) {
      setLogLines(value)
      fetchLogs(value)
    }
  }

  const fetchChartData = async () => {
    setChartLoading(true)
    try {
      // 调用新的统计接口获取最近7天的 token 消耗数据
      const response = await logApi.getTokenStats()
      const statsData = (response.data as any)?.data || response.data || {}
      
      // 计算最近7天的日期范围（包括今天）
      const today = dayjs()
      const dateMap = new Map<string, { count: number; tokens: number }>()
      
      // 初始化最近7天的数据（从6天前到今天，共7天）
      // 同时保存完整的日期对象用于比较
      const dateObjects: { dateStr: string; dateObj: dayjs.Dayjs }[] = []
      for (let i = 6; i >= 0; i--) {
        const dateObj = today.subtract(i, 'day')
        const dateStr = dateObj.format('MM-DD')
        dateMap.set(dateStr, { count: 0, tokens: 0 })
        dateObjects.push({ dateStr, dateObj })
      }

      // 处理接口返回的数据
      // 数据格式：数组 [{ date: 'YYYY-MM-DD', total_tokens_consumed: number, total_api_calls: number }, ...]
      
      if (Array.isArray(statsData)) {
        // 数组格式
        statsData.forEach((item: any) => {
          const dateStr = item.date || item.Date || item.time || item.Time
          if (!dateStr) return
          
          try {
            // 解析日期（格式为 YYYY-MM-DD）
            const dateObj = dayjs(dateStr)
            
            if (dateObj.isValid()) {
              const formattedDate = dateObj.format('MM-DD')
              if (dateMap.has(formattedDate)) {
                const existing = dateMap.get(formattedDate)!
                // 使用实际的字段名：total_api_calls 和 total_tokens_consumed
                existing.count += item.total_api_calls || item.count || 0
                existing.tokens += item.total_tokens_consumed || item.tokens || item.Tokens || 0
                dateMap.set(formattedDate, existing)
              }
            }
          } catch (e) {
            // 忽略解析错误
            console.warn('解析日期失败:', dateStr, e)
          }
        })
      } else if (typeof statsData === 'object' && statsData !== null) {
        // 对象格式（向后兼容）
        Object.keys(statsData).forEach((key: string) => {
          const item = statsData[key]
          if (!item) return
          
          try {
            // 尝试解析日期键
            let dateObj = dayjs(key)
            if (!dateObj.isValid()) {
              dateObj = dayjs(key, 'MM-DD')
            }
            
            if (dateObj.isValid()) {
              const formattedDate = dateObj.format('MM-DD')
              if (dateMap.has(formattedDate)) {
                const existing = dateMap.get(formattedDate)!
                existing.count += (item.total_api_calls || item.count || 0)
                existing.tokens += (item.total_tokens_consumed || item.tokens || item.Tokens || 0)
                dateMap.set(formattedDate, existing)
              }
            }
          } catch (e) {
            // 忽略解析错误
            console.warn('解析日期失败:', key, e)
          }
        })
      }

      // 转换为图表数据格式，按日期排序（从早到晚）
      // 使用保存的日期对象进行排序，确保跨年时也能正确排序
      const chartDataArray: ChartData[] = dateObjects
        .map(({ dateStr, dateObj }) => ({
          date: dateStr,
          count: dateMap.get(dateStr)?.count || 0,
          tokens: dateMap.get(dateStr)?.tokens || 0,
          _sortKey: dateObj.valueOf(), // 用于排序的时间戳
        }))
        .sort((a, b) => a._sortKey - b._sortKey)
        .map(({ date, count, tokens }) => ({ date, count, tokens }))

      setChartData(chartDataArray)
    } catch (error) {
      console.error('获取图表数据失败:', error)
      message.error('获取图表数据失败')
    } finally {
      setChartLoading(false)
    }
  }

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>仪表盘</h1>
      <Spin spinning={loading}>
        <Row gutter={16}>
          <Col span={6}>
            <Card>
              <Statistic
                title="API Keys"
                value={stats.apiKeys}
                prefix={<KeyOutlined />}
                precision={0}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="流程配置"
                value={stats.workflows}
                prefix={<ApartmentOutlined />}
                precision={0}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Prompt 模板"
                value={stats.prompts}
                prefix={<FileTextOutlined />}
                precision={0}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="模型参数"
                value={stats.modelParameters}
                prefix={<SettingOutlined />}
                precision={0}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
        </Row>
      </Spin>

      {/* 图表区域 */}
      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={12}>
          <Card 
            title="最近一周模型调用次数"
            loading={chartLoading}
          >
            <Column
              data={chartData}
              xField="date"
              yField="count"
              color="#1890ff"
              scale={{
                count: {
                  type: 'log',
                  base: 10,
                },
              }}
              xAxis={false}
              yAxis={{
                label: {
                  style: {
                    fontSize: 12,
                  },
                  formatter: (value: number) => {
                    if (value >= 1000000) {
                      return `${(value / 1000000).toFixed(1)}M`
                    } else if (value >= 1000) {
                      return `${(value / 1000).toFixed(1)}K`
                    }
                    return value.toString()
                  },
                },
              }}
              onReady={(plot: any) => {
                try {
                  // 尝试多种方式设置对数刻度
                  if (plot?.chart) {
                    const chart = plot.chart
                    chart.scale('count', {
                      type: 'log',
                      base: 10,
                    })
                    chart.render()
                  } else if (plot?.getChart) {
                    const chart = plot.getChart()
                    chart.scale('count', {
                      type: 'log',
                      base: 10,
                    })
                    chart.render()
                  } else if (plot?.update) {
                    plot.update({
                      scale: {
                        count: {
                          type: 'log',
                          base: 10,
                        },
                      },
                    })
                  }
                  // 调试信息
                  console.log('Plot object:', plot)
                } catch (e) {
                  console.error('设置对数刻度失败:', e)
                }
              }}
              height={300}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card 
            title="最近一周Token消耗量"
            loading={chartLoading}
          >
            <Line
              data={chartData}
              xField="date"
              yField="tokens"
              smooth={true}
              color="#52c41a"
              scale={{
                tokens: {
                  type: 'log',
                  base: 10,
                },
              }}
              point={{
                size: 5,
                shape: 'circle',
              }}
              label={{
                position: 'top',
                style: {
                  fill: '#666',
                  fontSize: 12,
                },
                formatter: (datum: any) => {
                  return datum.tokens ? datum.tokens.toLocaleString() : ''
                },
              }}
              xAxis={{
                reverse: false,
                label: {
                  autoRotate: false,
                  style: {
                    fontSize: 12,
                  },
                  formatter: (text: string) => {
                    if (!text) return ''
                    const date = dayjs(text)
                    return date.isValid() ? date.format('MM-DD') : text
                  },
                },
              }}
              yAxis={{
                label: {
                  style: {
                    fontSize: 12,
                  },
                  formatter: (value: number) => {
                    if (value >= 1000000) {
                      return `${(value / 1000000).toFixed(1)}M`
                    } else if (value >= 1000) {
                      return `${(value / 1000).toFixed(1)}K`
                    }
                    return value.toString()
                  },
                },
              }}
              onReady={(plot: any) => {
                try {
                  // 尝试多种方式设置对数刻度
                  if (plot?.chart) {
                    const chart = plot.chart
                    chart.scale('tokens', {
                      type: 'log',
                      base: 10,
                    })
                    chart.render()
                  } else if (plot?.getChart) {
                    const chart = plot.getChart()
                    chart.scale('tokens', {
                      type: 'log',
                      base: 10,
                    })
                    chart.render()
                  } else if (plot?.update) {
                    plot.update({
                      scale: {
                        tokens: {
                          type: 'log',
                          base: 10,
                        },
                      },
                    })
                  }
                  // 调试信息
                  console.log('Plot object:', plot)
                } catch (e) {
                  console.error('设置对数刻度失败:', e)
                }
              }}
              height={300}
            />
          </Card>
        </Col>
      </Row>
      
      {/* 日志列表 */}
      <Card 
        title={
          <Space>
            <FileSearchOutlined />
            <span>日志记录</span>
          </Space>
        }
        extra={
          <Space>
            <span>查询总数：</span>
            <InputNumber
              min={1}
              max={1000}
              value={logLines}
              onChange={handleLogLinesChange}
              style={{ width: 100 }}
            />
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => fetchLogs()}
              loading={logLoading}
            >
              刷新
            </Button>
          </Space>
        }
        style={{ marginTop: 24 }}
      >
        <Table
          columns={[
            {
              title: '编号',
              dataIndex: 'lineNumber',
              key: 'lineNumber',
              width: 80,
              align: 'right',
            },
            {
              title: '时间',
              dataIndex: 'Time',
              key: 'Time',
              width: 200,
              render: (text: string) => text ? new Date(text).toLocaleString('zh-CN') : '-',
            },
            {
              title: '状态',
              dataIndex: 'Status',
              key: 'Status',
              width: 100,
              align: 'center',
              render: (status: number | null) => {
                if (status === null || status === undefined) return '-'
                let displayText = status.toString()
                if (status === 200) {
                  displayText = 'Success'
                }
                const color = status >= 200 && status < 300 ? '#52c41a' : status >= 400 ? '#ff4d4f' : '#faad14'
                return <span style={{ color, fontWeight: 'bold' }}>{displayText}</span>
              },
            },
            {
              title: '模型',
              dataIndex: 'Model',
              key: 'Model',
              width: 250,
              ellipsis: true,
              render: (text: string) => text || '-',
            },
            {
              title: 'Tokens',
              dataIndex: 'Tokens',
              key: 'Tokens',
              width: 100,
              align: 'right',
              render: (tokens: number | null) => {
                if (tokens === null || tokens === undefined) return '-'
                return tokens.toLocaleString()
              },
            },
            {
              title: '日志内容',
              dataIndex: 'content',
              key: 'content',
              render: (text: string) => text ? (
                <Tooltip 
                  title={
                    <pre style={{ 
                      margin: 0, 
                      fontFamily: 'monospace', 
                      fontSize: '12px', 
                      whiteSpace: 'pre-wrap',
                      maxHeight: '300px',
                      overflowY: 'auto',
                      padding: '8px',
                    }}>
                      {text}
                    </pre>
                  } 
                  placement="topLeft"
                  overlayInnerStyle={{
                    maxWidth: '600px',
                  }}
                >
                  <div style={{ 
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    fontFamily: 'monospace',
                    fontSize: '12px',
                    cursor: 'pointer',
                  }}>
                    {text}
                  </div>
                </Tooltip>
              ) : '-',
            },
          ]}
          dataSource={logData}
          loading={logLoading}
          rowKey="key"
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            total: logData.length,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total: number) => `共 ${total} 条日志`,
            onChange: (page, newPageSize) => {
              setCurrentPage(page)
              if (newPageSize && newPageSize !== pageSize) {
                setPageSize(newPageSize)
                setCurrentPage(1) // 切换每页条数时回到第一页
              }
            },
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
          scroll={{ y: 600 }}
        />
      </Card>
    </div>
  )
}

export default Dashboard