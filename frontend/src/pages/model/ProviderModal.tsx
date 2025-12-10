import React, { useState, useEffect } from 'react';
import { Modal, Form, Input, Button, Select, Checkbox, InputNumber } from 'antd';
import type { CheckboxChangeEvent } from 'antd/es/checkbox';
import { 
  Settings,
  Brain,
  Save,
  Plus,
  AlertCircle,
  Loader2,
  Trash2,
  Eye
} from 'lucide-react';

// 类型定义
interface ModelConfiguration {
  name: string;
  max_input_tokens: number;
  supports_function_calling: boolean;
}

interface LLMProvider {
  id: number;
  name: string;
  provider: string;
  api_key?: string;
  api_base?: string;
  api_version?: string;
  custom_config?: Record<string, string>;
  default_model_name: string;
  fast_default_model_name?: string;
  deployment_name?: string;
  default_vision_model?: string;
  model_configurations: ModelConfiguration[];
  category: string;  // general, professional
  is_default_provider?: boolean;
  is_default_vision_provider?: boolean;
  created_at?: string;
  updated_at?: string;
}

interface ProviderType {
  value: string;
  label: string;
  description: string;
}


interface ProviderModalProps {
  isOpen: boolean;
  mode: 'create' | 'edit';
  provider?: LLMProvider | null;
  variant?: 'glassmorphism' | 'neumorphism';
  onClose: () => void;
  onSave: (provider: LLMProvider) => void;
  onTest?: (provider: LLMProvider) => Promise<void>;
  providerTypes: ProviderType[];
}

const ProviderModal: React.FC<ProviderModalProps> = ({
  isOpen,
  mode,
  provider,
  onClose,
  onSave,
  providerTypes,
}) => {
  const [form, setForm] = useState<LLMProvider>({
    id: 0,
    name: '',
    provider: '',
    api_key: '',
    api_base: '',
    api_version: '',
    custom_config: {},
    default_model_name: '',
    fast_default_model_name: '',
    deployment_name: '',
    default_vision_model: '',
    model_configurations: [],
    category: 'general',
    is_default_provider: false,
    is_default_vision_provider: false,
    created_at: '',
    updated_at: '',
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // 保存原始的脱敏密钥，用于判断用户是否修改了密钥
  const [originalMaskedApiKey, setOriginalMaskedApiKey] = useState<string>('');
  const [apiKeyModified, setApiKeyModified] = useState(false);
  
  // 修改：模型类型选择状态，至少选择一个
  const [modelTypeSelection, setModelTypeSelection] = useState<{
    default: boolean;
    vision: boolean;
  }>({
    default: true, // 默认至少选择默认模型
    vision: false,
  });


  // 初始化表单数据
  useEffect(() => {
    if (mode === 'edit' && provider) {
      setForm({
        ...provider,
        model_configurations: provider.model_configurations || [],
        custom_config: provider.custom_config || {},
        is_default_provider: provider.is_default_provider || false,
        is_default_vision_provider: provider.is_default_vision_provider || false,
      });
      
      // 保存原始的脱敏密钥，用于后续判断用户是否修改了密钥
      if (provider.api_key) {
        setOriginalMaskedApiKey(provider.api_key);
      }
      setApiKeyModified(false);
      
      // 根据现有数据设置模型类型选择
      setModelTypeSelection({
        default: !!provider.default_model_name,
        vision: !!provider.default_vision_model,
      });
      
      // 调试：打印初始化数据
      console.log('编辑模式初始化数据:', {
        provider,
        apiKey: provider.api_key?.includes('****') ? '脱敏密钥' : '明文密钥',
        modelTypeSelection: {
          default: !!provider.default_model_name,
          vision: !!provider.default_vision_model,
        }
      });
    } else {
      // 重置为空表单
      setForm({
        id: 0,
        name: '',
        provider: '',
        api_key: '',
        api_base: '',
        api_version: '',
        custom_config: {},
        default_model_name: '',
        fast_default_model_name: '',
        deployment_name: '',
        default_vision_model: '',
        model_configurations: [],
        category: 'general',
        is_default_provider: false,
        is_default_vision_provider: false,
        created_at: '',
        updated_at: '',
      });
      
      setOriginalMaskedApiKey('');
      setApiKeyModified(false);
      
      setModelTypeSelection({
        default: true, // 创建时默认选择默认模型
        vision: false,
      });
    }
    setError(null);
  }, [mode, provider, isOpen]);

  // 处理模型类型选择变化 - 确保至少选择一个
  const handleModelTypeChange = (type: 'default' | 'vision', checked: boolean) => {
    // 如果尝试取消默认模型，但视觉模型也没有选择，则不允许
    if (type === 'default' && !checked && !modelTypeSelection.vision) {
      setError('至少需要选择一个模型类型（默认模型或视觉模型）');
      return;
    }
    
    // 如果尝试取消视觉模型，但默认模型也没有选择，则不允许
    if (type === 'vision' && !checked && !modelTypeSelection.default) {
      setError('至少需要选择一个模型类型（默认模型或视觉模型）');
      return;
    }

    setModelTypeSelection(prev => ({
      ...prev,
      [type]: checked
    }));
    
    // 根据选择清空相应的模型字段
    if (!checked) {
      if (type === 'default') {
        setForm(prev => ({ ...prev, default_model_name: '' }));
      } else if (type === 'vision') {
        setForm(prev => ({ ...prev, default_vision_model: '' }));
      }
    }
    
    // 清除错误信息
    setError(null);
  };

  // 添加模型配置
  const addModelConfiguration = () => {
    const newConfig: ModelConfiguration = {
      name: '',
      max_input_tokens: 4096,
      supports_function_calling: false
    };
    setForm(prev => ({
      ...prev,
      model_configurations: [...prev.model_configurations, newConfig]
    }));
  };

  // 更新模型配置
  const updateModelConfiguration = (index: number, field: keyof ModelConfiguration, value: any) => {
    setForm(prev => ({
      ...prev,
      model_configurations: prev.model_configurations.map((config, i) => 
        i === index ? { ...config, [field]: value } : config
      )
    }));
  };

  // 删除模型配置
  const removeModelConfiguration = (index: number) => {
    setForm(prev => ({
      ...prev,
      model_configurations: prev.model_configurations.filter((_, i) => i !== index)
    }));
  };

  // 处理保存
  const handleSave = async () => {
    setError(null);
    
    // 验证必填字段
    if (mode === 'create') {
      if (!form.name || !form.provider) {
        setError('请填写模型名称和类型');
        return;
      }
    } else {
      if (!form.name || !form.provider) {
        setError('请填写模型名称和类型');
        return;
      }
    }

    // 验证至少选择一个模型类型
    if (!modelTypeSelection.default && !modelTypeSelection.vision) {
      setError('至少需要选择一个模型类型（默认模型或视觉模型）');
      return;
    }

    // 验证模型类型选择与相应字段的匹配
    if (modelTypeSelection.default && !form.default_model_name) {
      setError('选择了默认模型类型，请填写默认模型名称');
      return;
    }
    
    if (modelTypeSelection.vision && !form.default_vision_model) {
      setError('选择了视觉模型类型，请填写视觉模型名称');
      return;
    }

    // 验证模型配置
    for (let i = 0; i < form.model_configurations.length; i++) {
      const config = form.model_configurations[i];
      if (!config.name) {
        setError(`模型配置 ${i + 1} 的名称不能为空`);
        return;
      }
      if (!config.max_input_tokens || config.max_input_tokens <= 0) {
        setError(`模型配置 ${i + 1} 的最大Token数必须大于0`);
        return;
      }
    }

    // 准备提交的数据
    const submitData = { ...form };
    
    // 处理API密钥：如果是编辑模式且密钥未修改（脱敏格式），保持原值让后端识别
    // 后端会检查是否包含****，如果包含则不更新密钥
    if (mode === 'edit' && originalMaskedApiKey.includes('****') && !apiKeyModified) {
      // 保持脱敏密钥，后端会识别并跳过更新
      submitData.api_key = originalMaskedApiKey;
    }
    // 如果是新密钥或已修改的密钥，直接提交，后端会进行加密
    
    // 调试：打印表单数据
    console.log('提交的表单数据:', {
      ...submitData,
      modelTypeSelection,
      apiKeyModified: mode === 'edit' ? apiKeyModified : 'N/A',
      apiKeyStatus: submitData.api_key?.includes('****') ? '脱敏（不更新）' : '明文（需加密）'
    });

    try {
      setLoading(true);
      await onSave(submitData);
      onClose();
    } catch (error) {
      setError(error instanceof Error ? error.message : '保存失败');
    } finally {
      setLoading(false);
    }
  };


  return (
    <Modal
      title={
        <div className="flex items-center space-x-2">
         
          <span>{mode === 'create' ? '创建模型参数' : `编辑模型参数: ${provider?.name || ''}`}</span>
        </div>
      }
      open={isOpen}
      onCancel={onClose}
      footer={null}
      width={800}
      className="create-folder-modal"
      destroyOnClose
    >
      <div className="px-4" style={{height: 500, overflowY: 'auto'}}>
        {/* 错误提示 */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center">
            <AlertCircle className="w-5 h-5 text-red-600 mr-3" />
            <span className="text-red-800 text-sm">{error}</span>
          </div>
        )}

        <Form
          layout="vertical"
          onFinish={handleSave}
          autoComplete="off"
        >
          {/* 基本信息 */}
          <div className="space-y-4 mb-6">
            <h3 className="text-lg font-semibold flex items-center text-gray-900">
              <Settings className="w-5 h-5 mr-2 text-blue-600" />
              基本信息
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Form.Item
                label="模型名称"
                name="name"
                rules={[{ required: true, message: '请输入模型名称' }]}
                initialValue={form.name}
              >
                <Input 
                  placeholder="输入模型名称"
                  value={form.name}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(prev => ({ ...prev, name: e.target.value }))}
                />
              </Form.Item>
              
              <Form.Item
                label="服务商类型"
                name="provider"
                rules={[{ required: true, message: '请选择服务商类型' }]}
                initialValue={form.provider}
              >
                <Select
                  placeholder="选择服务商类型"
                  value={form.provider}
                  onChange={(value: string) => setForm(prev => ({ ...prev, provider: value }))}
                >
                  {providerTypes.map((type) => (
                    <Select.Option key={type.value} value={type.value}>
                      {type.label} - {type.description}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </div>

            

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Form.Item
                label="API Key"
                name="api_key"
                initialValue={form.api_key}
                extra={mode === 'edit' && originalMaskedApiKey.includes('****') && !apiKeyModified
                  ? '当前显示的是脱敏后的密钥。如需修改，请输入新密钥。'
                  : null
                }
              >
                <Input.Password 
                  placeholder={mode === 'edit' && originalMaskedApiKey.includes('****')
                    ? '保持原密钥不变或输入新密钥'
                    : '输入API密钥'
                  }
                  value={form.api_key || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                    const newValue = e.target.value;
                    setForm(prev => ({ ...prev, api_key: newValue }));
                    
                    // 如果是编辑模式且有原始密钥，检查用户是否修改了密钥
                    if (mode === 'edit' && originalMaskedApiKey) {
                      // 如果用户输入了新内容（不等于原始脱敏密钥），标记为已修改
                      setApiKeyModified(newValue !== originalMaskedApiKey && newValue !== '');
                    }
                  }}
                  visibilityToggle={false}
                />
              </Form.Item>
              
              <Form.Item
                label="API Base URL"
                name="api_base"
                initialValue={form.api_base}
              >
                <Input 
                  placeholder="输入API基础URL（可选）"
                  value={form.api_base || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(prev => ({ ...prev, api_base: e.target.value }))}
                />
              </Form.Item>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Form.Item
                label="模型类别"
                name="category"
                rules={[{ required: true, message: '请选择模型类别' }]}
                initialValue={form.category}
              >
                <Select
                  placeholder="选择模型类别"
                  value={form.category}
                  onChange={(value: string) => setForm(prev => ({ ...prev, category: value }))}
                >
                  <Select.Option value="general">通用模型</Select.Option>
                  <Select.Option value="professional">专有模型</Select.Option>
                </Select>
              </Form.Item>
              
              <Form.Item
                label="温度"
                name="temperature"
                initialValue={form.custom_config?.temperature ? parseFloat(form.custom_config.temperature) : undefined}
                tooltip="控制输出的随机性，范围 0-1，值越大输出越随机"
              >
                <InputNumber
                  placeholder="输入温度值 (0-1)"
                  value={form.custom_config?.temperature ? parseFloat(form.custom_config.temperature) : undefined}
                  onChange={(value: number | null) => {
                    setForm(prev => {
                      const newCustomConfig = { ...prev.custom_config };
                      if (value !== null && value !== undefined) {
                        newCustomConfig.temperature = value.toString();
                      } else {
                        delete newCustomConfig.temperature;
                      }
                      return {
                        ...prev,
                        custom_config: newCustomConfig
                      };
                    });
                  }}
                  min={0}
                  max={1}
                  step={0.1}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </div>
          </div>

          {/* 核心模型配置 */}
          <div className="space-y-4 mb-6">
            <h3 className="text-lg font-semibold flex items-center text-gray-900">
              <Brain className="w-5 h-5 mr-2 text-blue-600" />
              核心模型配置
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* 默认模型选择 */}
              <div className="p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center space-x-3  mb-3">
                  <Checkbox
                    
                    checked={modelTypeSelection.default}
                    onChange={(e: CheckboxChangeEvent) => handleModelTypeChange('default', e.target.checked)}
                  />
                  <label className="flex items-center ml-2 space-x-2 cursor-pointer">
                    <Brain className="w-4 h-4 text-blue-500 " />
                    <span className="font-medium">默认模型</span>
                    <span className="text-red-500">*</span>
                  </label>
                </div>
                <p className="text-sm text-gray-600 mb-3">
                  主要的文本生成模型，用于一般性任务
                </p>
                {modelTypeSelection.default && (
                  <Form.Item
                    label="默认模型名称"
                    name="default_model_name"
                    rules={[{ required: true, message: '请输入默认模型名称' }]}
                    initialValue={form.default_model_name}
                  >
                    <Input 
                      placeholder="输入默认模型名称"
                      value={form.default_model_name}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(prev => ({ ...prev, default_model_name: e.target.value }))}
                    />
                  </Form.Item>
                )}
              </div>

              {/* 视觉模型选择 */}
              <div className="p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center space-x-3 mb-3">
                  <Checkbox
                    checked={modelTypeSelection.vision}
                    onChange={(e: CheckboxChangeEvent) => handleModelTypeChange('vision', e.target.checked)}
                  />
                  <label className="flex items-center ml-2 space-x-2 cursor-pointer">
                    <Eye className="w-4 h-4 text-purple-500" />
                    <span className="font-medium">视觉模型</span>
                  </label>
                </div>
                <p className="text-sm text-gray-600 mb-3">
                  支持图像理解和处理的模型
                </p>
                {modelTypeSelection.vision && (
                  <Form.Item
                    label="视觉模型名称"
                    name="default_vision_model"
                    rules={[{ required: true, message: '请输入视觉模型名称' }]}
                    initialValue={form.default_vision_model}
                  >
                    <Input 
                      placeholder="输入视觉模型名称"
                      value={form.default_vision_model || ''}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(prev => ({ ...prev, default_vision_model: e.target.value }))}
                    />
                  </Form.Item>
                )}
              </div>
            </div>
            
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>注意：</strong> 至少需要选择一个模型类型。默认模型是必需的，视觉模型是可选的。
              </p>
            </div>
          </div>

          {/* 其他配置 */}
          <div className="space-y-4 mb-6">
            <h3 className="text-lg font-semibold flex items-center text-gray-900">
              <Settings className="w-5 h-5 mr-2 text-blue-600" />
              其他配置
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Form.Item
                label="快速模型"
                name="fast_default_model_name"
                initialValue={form.fast_default_model_name}
              >
                <Input 
                  placeholder="输入快速模型名称"
                  value={form.fast_default_model_name || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(prev => ({ ...prev, fast_default_model_name: e.target.value }))}
                />
              </Form.Item>
              
              <Form.Item
                label="API版本"
                name="api_version"
                initialValue={form.api_version}
              >
                <Input 
                  placeholder="输入API版本（可选）"
                  value={form.api_version || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(prev => ({ ...prev, api_version: e.target.value }))}
                />
              </Form.Item>
              
              <Form.Item
                label="部署名称"
                name="deployment_name"
                initialValue={form.deployment_name}
              >
                <Input 
                  placeholder="输入部署名称（可选）"
                  value={form.deployment_name || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm(prev => ({ ...prev, deployment_name: e.target.value }))}
                />
              </Form.Item>
            </div>
          </div>

         

          {/* 其他模型配置 */}
          <div className="space-y-4 mb-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold flex items-center text-gray-900">
                <Settings className="w-5 h-5 mr-2 text-blue-600" />
                其他模型配置
              </h3>
              <Button
                onClick={addModelConfiguration}
                className="flex items-center space-x-2"
                icon={<Plus className="w-4 h-4" />}
              >
                添加模型
              </Button>
            </div>
            
            <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
              <p className="text-sm text-gray-700">
                <strong>其他模型：</strong> 可以添加快速模型或其他特殊用途的模型配置。
              </p>
            </div>
            
            <div className="space-y-4">
              {form.model_configurations.map((config, index) => (
                <div key={index} className="p-4 border border-gray-200 rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium flex items-center">
                      <Settings className="w-4 h-4 mr-2 text-gray-500" />
                      模型配置 {index + 1}
                    </h4>
                    <Button
                      onClick={() => removeModelConfiguration(index)}
                      danger
                      className="flex items-center space-x-1"
                      icon={<Trash2 className="w-4 h-4" />}
                    >
                      删除
                    </Button>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <Form.Item
                      label="模型名称"
                      name={`model_config_${index}_name`}
                      rules={[{ required: true, message: '请输入模型名称' }]}
                      initialValue={config.name}
                    >
                      <Input 
                        placeholder="输入模型名称"
                        value={config.name}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateModelConfiguration(index, 'name', e.target.value)}
                      />
                    </Form.Item>
                    
                    <Form.Item
                      label="最大Token数"
                      name={`model_config_${index}_tokens`}
                      rules={[{ required: true, message: '请输入最大Token数' }]}
                      initialValue={config.max_input_tokens}
                    >
                      <Input 
                        type="number"
                        placeholder="输入最大Token数"
                        value={config.max_input_tokens}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateModelConfiguration(index, 'max_input_tokens', parseInt(e.target.value) || 0)}
                        min="1"
                      />
                    </Form.Item>
                  </div>
                  
                  <Form.Item>
                    <Checkbox
                      checked={config.supports_function_calling}
                      onChange={(e: CheckboxChangeEvent) => updateModelConfiguration(index, 'supports_function_calling', e.target.checked)}
                    >
                      支持函数调用
                    </Checkbox>
                  </Form.Item>
                </div>
              ))}
            </div>
          </div>
        </Form>
      </div>
      
      <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 px-4">
        <Button
          onClick={onClose}
          disabled={loading}
        >
          取消
        </Button>
        <Button
          type="primary"
          onClick={handleSave}
          loading={loading}
          disabled={!form.name?.trim() || !form.provider?.trim()}
        >
          {loading ? (
            <div className="flex items-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>保存中...</span>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <Save className="w-4 h-4" />
              <span>{mode === 'create' ? '创建' : '保存'}</span>
            </div>
          )}
        </Button>
      </div>
    </Modal>
  );
};

export default ProviderModal;
