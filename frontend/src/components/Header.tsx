import React from 'react'
import { Layout, Breadcrumb, Avatar, Dropdown, Space, message } from 'antd'
import { UserOutlined, LogoutOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import type { MenuProps } from 'antd'

const { Header: AntHeader } = Layout

const Header: React.FC = () => {
  const navigate = useNavigate()
  const username = localStorage.getItem('username') || 'Admin'

  const handleLogout = () => {
    localStorage.removeItem('isAuthenticated')
    localStorage.removeItem('username')
    message.success('已退出登录')
    navigate('/login')
  }

  const items: MenuProps['items'] = [
    {
      key: 'user',
      label: `当前用户: ${username}`,
      disabled: true,
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <AntHeader style={{ 
      position: 'fixed',
      top: 0,
      right: 0,
      left: 200,
      zIndex: 1000,
      padding: '0 24px', 
      background: '#fff', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'space-between',
      borderBottom: '1px solid #f0f0f0',
      height: 64,
      lineHeight: '64px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
    }}>
      <Breadcrumb>
        <Breadcrumb.Item></Breadcrumb.Item>
      </Breadcrumb>
      <Space>
        <Dropdown menu={{ items }} placement="bottomRight">
          <Avatar icon={<UserOutlined />} />
        </Dropdown>
      </Space>
    </AntHeader>
  )
}

export default Header
