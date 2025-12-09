import React, { useState } from 'react'
import { Form, Input, Button, Card, Typography, message } from 'antd'
import { LockOutlined, UserOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Text } = Typography

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const [form] = Form.useForm()

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      // TODO: 调用后端登录API
      console.log('登录信息:', values)
      
      // 模拟登录验证
      if (values.username === 'admin' && values.password === 'admin123') {
        message.success('登录成功')
        // 保存登录状态到本地存储
        localStorage.setItem('isAuthenticated', 'true')
        localStorage.setItem('username', values.username)
        
        // 跳转到仪表盘
        navigate('/')
      } else {
        message.error('用户名或密码错误')
      }
    } catch (error) {
      message.error('登录失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: '#f0f2f5',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <Card 
        style={{
          width: '100%',
          maxWidth: 420,
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.08)',
          borderRadius: '8px'
        }}
        bodyStyle={{ padding: '40px' }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            width: 64,
            height: 64,
            background: '#fff',
            borderRadius: '50%',
            margin: '0 auto 20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 28,
            color: '#1890ff',
            border: '2px solid #1890ff'
          }}>
            <LockOutlined />
          </div>
          
          <Text type="secondary" style={{ fontSize: 14 }}>
          新华大模型文风配置管理系统
          </Text>
        </div>

        <Form
          form={form}
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          layout="vertical"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少3个字符' }
            ]}
          >
            <Input
              prefix={<UserOutlined style={{ color: '#bfbfbf' }} />}
              placeholder="请输入用户名"
              style={{ borderRadius: 6 }}
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6个字符' }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: '#bfbfbf' }} />}
              placeholder="请输入密码"
              style={{ borderRadius: 6 }}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{
                height: 45,
                fontSize: 16,
                borderRadius: 6
              }}
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <div style={{ 
          textAlign: 'center', 
          marginTop: 24,
          padding: '16px',
          background: '#fafafa',
          borderRadius: 6,
          border: '1px solid #f0f0f0'
        }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            默认账号: admin / admin123
          </Text>
        </div>
      </Card>
    </div>
  )
}

export default Login
