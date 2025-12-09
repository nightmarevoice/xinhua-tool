import React, { ReactNode } from 'react'
import {
  DashboardOutlined,
  KeyOutlined,
  ApartmentOutlined,
  FileTextOutlined,
  SettingOutlined,
  ExperimentOutlined,
  SafetyOutlined,
  HistoryOutlined
} from '@ant-design/icons'
import { RouteObject } from 'react-router-dom'
import Dashboard from '../pages/Dashboard'
import ApiKeyPage from '../pages/apikey/ApiKeyPage'
import WorkflowPage from '../pages/workflow/WorkflowPage'
import PromptPage from '../pages/prompt/PromptPage'
import ModelPage from '../pages/model/ModelPage'
import ChatTestPage from '../pages/ChatTestPage'
import SecurityCenterPage from '../pages/security/SecurityCenterPage'
import ChatLogPage from '../pages/ChatLogPage'
import Login from '../pages/Login'
import ProtectedRoute from '../components/ProtectedRoute'
import MainLayout from '../layouts/MainLayout'

export interface RouteConfig {
  key: string
  path: string
  label: string
  icon: ReactNode
  component: React.ComponentType
}

export const routeConfig: RouteConfig[] = [
  {
    key: '/',
    path: '/',
    label: '仪表盘',
    icon: React.createElement(DashboardOutlined),
    component: Dashboard
  },
  {
    key: '/apikeymanagement',
    path: '/apikeymanagement',
    label: 'API Key 管理',
    icon: React.createElement(KeyOutlined),
    component: ApiKeyPage
  },
  {
    key: '/workflow',
    path: '/workflow',
    label: '流程配置',
    icon: React.createElement(ApartmentOutlined),
    component: WorkflowPage
  },
  {
    key: '/prompt',
    path: '/prompt',
    label: 'Prompt 配置',
    icon: React.createElement(FileTextOutlined),
    component: PromptPage
  },
  {
    key: '/model',
    path: '/model',
    label: '模型参数配置',
    icon: React.createElement(SettingOutlined),
    component: ModelPage
  },
  {
    key: '/chattest',
    path: '/chattest',
    label: '智能生成新闻',
    icon: React.createElement(ExperimentOutlined),
    component: ChatTestPage
  },
  {
    key: '/chat-logs',
    path: '/chat-logs',
    label: '智能新闻记录',
    icon: React.createElement(HistoryOutlined),
    component: ChatLogPage
  },
  {
    key: '/security',
    path: '/security',
    label: '安全中心',
    icon: React.createElement(SafetyOutlined),
    component: SecurityCenterPage
  }
]

// 导出菜单项（用于Sidebar）
export const menuItems = routeConfig.map(route => ({
  key: route.key,
  icon: route.icon,
  label: route.label
}))

// 导出路由配置（用于App.tsx）
export const routes: RouteObject[] = [
  {
    path: '/login',
    element: React.createElement(Login)
  },
  {
    path: '/',
    element: React.createElement(ProtectedRoute, {
      children: React.createElement(MainLayout)
    }),
    children: routeConfig.map(route => ({
      path: route.path === '/' ? '' : route.path.replace('/', ''),
      element: React.createElement(route.component)
    }))
  }
]
