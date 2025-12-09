import React from 'react'
import { Layout, Menu } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import { menuItems } from '../config/routes'

const { Sider } = Layout

const Sidebar: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <Sider 
      width={200} 
      style={{ 
        background: '#fff',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        zIndex: 1001
      }}
    >
      <div style={{ 
        height: 32, 
        margin: 16, 
        background: '#667eea',
        padding:4, 
        borderRadius: 8,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: 'bold',
        fontSize: 16,
        color: '#fff',
        boxShadow: '0 2px 8px rgba(102, 126, 234, 0.3)'
      }}>
        新华大模型文风配置
      </div>
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        style={{ height: '100%', borderRight: 0 }}
        items={menuItems}
        onClick={({ key }: { key: string }) => navigate(key)}
      />
    </Sider>
  )
}

export default Sidebar
