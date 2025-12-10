import React, { useState, useRef, useEffect } from 'react';
import { Layout, Card, Button, Space, Typography, Spin, message, Image } from 'antd';
import { AudioOutlined, PlayCircleOutlined, PauseCircleOutlined, 
         LeftOutlined, RightOutlined, DownloadOutlined } from '@ant-design/icons';
import AudioRecorder from './components/AudioRecorder';
import HistoryManager from './components/HistoryManager';
import { audioToImage } from './services/api';
import './App.css';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentImage, setCurrentImage] = useState(null);
  const [currentText, setCurrentText] = useState('');
  const [history, setHistory] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(-1);

  // 加载历史记录
  useEffect(() => {
    const savedHistory = HistoryManager.loadHistory();
    if (savedHistory.length > 0) {
      setHistory(savedHistory);
      setCurrentIndex(savedHistory.length - 1);
      const lastItem = savedHistory[savedHistory.length - 1];
      setCurrentImage(lastItem.imageData);
      setCurrentText(lastItem.text);
    }
  }, []);

  // 处理录音完成
  const handleRecordingComplete = async (audioBlob) => {
    setIsProcessing(true);
    message.info('正在处理音频，请稍候...');

    try {
      const result = await audioToImage(audioBlob);
      
      if (result.success) {
        // 保存到历史记录
        const newItem = {
          id: Date.now(),
          text: result.text,
          imageData: result.imageData,
          imageUrl: result.imageUrl,
          timestamp: result.timestamp
        };
        
        const updatedHistory = [...history, newItem];
        setHistory(updatedHistory);
        setCurrentIndex(updatedHistory.length - 1);
        HistoryManager.saveHistory(updatedHistory);
        
        // 更新当前显示
        setCurrentImage(result.imageData);
        setCurrentText(result.text);
        
        message.success('图片生成成功！');
      } else {
        message.error(result.error || '处理失败');
      }
    } catch (error) {
      console.error('处理错误:', error);
      message.error(error.message || '处理失败，请检查网络连接');
    } finally {
      setIsProcessing(false);
    }
  };

  // 切换到上一张
  const handlePrevious = () => {
    if (currentIndex > 0) {
      const newIndex = currentIndex - 1;
      setCurrentIndex(newIndex);
      const item = history[newIndex];
      setCurrentImage(item.imageData);
      setCurrentText(item.text);
    } else {
      message.info('已经是第一张了');
    }
  };

  // 切换到下一张
  const handleNext = () => {
    if (currentIndex < history.length - 1) {
      const newIndex = currentIndex + 1;
      setCurrentIndex(newIndex);
      const item = history[newIndex];
      setCurrentImage(item.imageData);
      setCurrentText(item.text);
    } else {
      message.info('已经是最后一张了');
    }
  };

  // 下载当前图片
  const handleDownload = () => {
    if (currentImage) {
      const link = document.createElement('a');
      link.href = currentImage;
      link.download = `generated-image-${Date.now()}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      message.success('图片已下载');
    }
  };

  return (
    <Layout className="app-layout">
      <Header className="app-header">
        <Title level={2} style={{ color: '#fff', margin: 0 }}>
          <AudioOutlined /> 语音转图片生成器
        </Title>
      </Header>
      
      <Content className="app-content">
        <div className="container">
          {/* 录音控制区域 */}
          <Card className="recorder-card" title="🎤 语音输入">
            <AudioRecorder
              isRecording={isRecording}
              onRecordingChange={setIsRecording}
              onRecordingComplete={handleRecordingComplete}
              disabled={isProcessing}
            />
          </Card>

          {/* 处理状态 */}
          {isProcessing && (
            <Card className="processing-card">
              <Space direction="vertical" align="center" size="large">
                <Spin size="large" />
                <Text>正在处理音频，生成图片中...</Text>
              </Space>
            </Card>
          )}

          {/* 结果显示区域 */}
          {(currentImage || currentText) && !isProcessing && (
            <Card 
              className="result-card" 
              title="🎨 生成结果"
              extra={
                <Space>
                  <Button 
                    icon={<LeftOutlined />} 
                    onClick={handlePrevious}
                    disabled={currentIndex <= 0}
                  >
                    上一张
                  </Button>
                  <Text type="secondary">
                    {history.length > 0 ? `${currentIndex + 1} / ${history.length}` : '0 / 0'}
                  </Text>
                  <Button 
                    icon={<RightOutlined />} 
                    onClick={handleNext}
                    disabled={currentIndex >= history.length - 1}
                  >
                    下一张
                  </Button>
                  <Button 
                    type="primary" 
                    icon={<DownloadOutlined />} 
                    onClick={handleDownload}
                  >
                    下载
                  </Button>
                </Space>
              }
            >
              {currentText && (
                <div className="text-result">
                  <Text strong>识别文字：</Text>
                  <Text>{currentText}</Text>
                </div>
              )}
              
              {currentImage && (
                <div className="image-result">
                  <Image
                    src={currentImage}
                    alt="生成的图片"
                    style={{ maxWidth: '100%', borderRadius: '8px' }}
                    preview={{
                      mask: '点击查看大图'
                    }}
                  />
                </div>
              )}
            </Card>
          )}

          {/* 空状态提示 */}
          {!currentImage && !isProcessing && (
            <Card className="empty-card">
              <Space direction="vertical" align="center" size="large">
                <Text type="secondary" style={{ fontSize: '16px' }}>
                  点击上方按钮开始录音，生成你的第一张图片吧！
                </Text>
              </Space>
            </Card>
          )}
        </div>
      </Content>
    </Layout>
  );
}

export default App;

