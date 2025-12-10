import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001/api';

/**
 * 发送音频文件，获取生成的图片
 * @param {Blob} audioBlob - 音频文件blob
 * @returns {Promise} 包含text和imageData的结果
 */
export async function audioToImage(audioBlob) {
  try {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');

    const response = await axios.post(
      `${API_BASE_URL}/audio-to-image`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000, // 60秒超时
      }
    );

    return response.data;
  } catch (error) {
    console.error('API调用错误:', error);
    
    if (error.response) {
      // 服务器返回了错误响应
      throw new Error(error.response.data?.error || '服务器错误');
    } else if (error.request) {
      // 请求已发出但没有收到响应
      throw new Error('网络错误，请检查后端服务是否运行');
    } else {
      // 其他错误
      throw new Error(error.message || '未知错误');
    }
  }
}

