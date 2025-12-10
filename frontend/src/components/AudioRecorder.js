import React, { useRef, useState, useEffect } from 'react';
import { Button, Space, Typography } from 'antd';
import { AudioOutlined, StopOutlined } from '@ant-design/icons';

const { Text } = Typography;

function AudioRecorder({ isRecording, onRecordingChange, onRecordingComplete, disabled }) {
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);

  // 计时器
  useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isRecording]);

  // 开始录音
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus' // 优先使用webm格式
      });

      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { 
          type: 'audio/webm;codecs=opus' 
        });
        
        // 停止所有音频轨道
        stream.getTracks().forEach(track => track.stop());
        
        // 调用完成回调
        onRecordingComplete(audioBlob);
        setRecordingTime(0);
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      onRecordingChange(true);
      setRecordingTime(0);
    } catch (error) {
      console.error('录音启动失败:', error);
      alert('无法访问麦克风，请检查权限设置');
    }
  };

  // 停止录音
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      onRecordingChange(false);
    }
  };

  // 格式化时间
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }} align="center">
      {!isRecording ? (
        <Button
          type="primary"
          size="large"
          icon={<AudioOutlined />}
          onClick={startRecording}
          disabled={disabled}
          style={{ height: '60px', fontSize: '18px', padding: '0 40px' }}
        >
          开始录音
        </Button>
      ) : (
        <>
          <Button
            type="primary"
            danger
            size="large"
            icon={<StopOutlined />}
            onClick={stopRecording}
            style={{ height: '60px', fontSize: '18px', padding: '0 40px' }}
          >
            停止录音
          </Button>
          <Text strong style={{ fontSize: '24px', color: '#ff4d4f' }}>
            ⏱️ {formatTime(recordingTime)}
          </Text>
        </>
      )}
      <Text type="secondary">
        {isRecording ? '正在录音中...' : '点击按钮开始录音，然后说出你想要生成的图片描述'}
      </Text>
    </Space>
  );
}

export default AudioRecorder;

