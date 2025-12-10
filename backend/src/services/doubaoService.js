const axios = require('axios');
const FormData = require('form-data');

class DoubaoService {
  constructor() {
    this.apiKey = process.env.DOUBAO_API_KEY;
    this.baseURL = process.env.DOUBAO_API_BASE_URL || 'https://ark.cn-beijing.volces.com/api/v3';
    
    if (!this.apiKey) {
      console.warn('⚠️  DOUBAO_API_KEY not found in environment variables');
    }
  }

  /**
   * 语音转文字（ASR）
   * @param {Buffer} audioBuffer - 音频文件buffer
   * @param {string} audioFormat - 音频格式 (wav, mp3, etc.)
   * @returns {Promise<string>} 识别的文字
   */
  async audioToText(audioBuffer, audioFormat = 'wav') {
    try {
      // 注意：这里需要根据豆包API的实际接口调整
      // 以下是示例实现，实际需要参考豆包官方文档
      
      const formData = new FormData();
      formData.append('audio', audioBuffer, {
        filename: `audio.${audioFormat}`,
        contentType: `audio/${audioFormat}`
      });
      formData.append('model', 'doubao-asr'); // 根据实际模型名称调整

      const response = await axios.post(
        `${this.baseURL}/audio/transcriptions`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            ...formData.getHeaders()
          }
        }
      );

      // 根据实际API响应格式调整
      return response.data.text || response.data.result || '';
    } catch (error) {
      console.error('语音转文字错误:', error.response?.data || error.message);
      throw new Error(`语音转文字失败: ${error.response?.data?.error?.message || error.message}`);
    }
  }

  /**
   * 文字生成图片
   * @param {string} text - 文字描述
   * @returns {Promise<{imageUrl: string, imageData: string}>} 生成的图片
   */
  async textToImage(text) {
    try {
      // 注意：这里需要根据豆包API的实际接口调整
      // 以下是示例实现，实际需要参考豆包官方文档
      
      const response = await axios.post(
        `${this.baseURL}/images/generations`,
        {
          model: 'doubao-image', // 根据实际模型名称调整
          prompt: text,
          n: 1,
          size: '1024x1024'
        },
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      // 根据实际API响应格式调整
      const imageUrl = response.data.data?.[0]?.url || response.data.url;
      const imageData = response.data.data?.[0]?.b64_json || '';

      // 如果返回的是URL，需要下载图片转换为base64
      let base64Data = imageData;
      if (imageUrl && !imageData) {
        const imageResponse = await axios.get(imageUrl, {
          responseType: 'arraybuffer'
        });
        base64Data = Buffer.from(imageResponse.data).toString('base64');
      }

      return {
        imageUrl: imageUrl || '',
        imageData: base64Data ? `data:image/png;base64,${base64Data}` : ''
      };
    } catch (error) {
      console.error('文字生成图片错误:', error.response?.data || error.message);
      throw new Error(`图片生成失败: ${error.response?.data?.error?.message || error.message}`);
    }
  }

  /**
   * 模拟API调用（用于测试，当没有真实API密钥时）
   */
  async mockAudioToText(audioBuffer) {
    // 模拟延迟
    await new Promise(resolve => setTimeout(resolve, 1000));
    return '这是一段测试文字，用于生成图片';
  }

  async mockTextToImage(text) {
    // 模拟延迟
    await new Promise(resolve => setTimeout(resolve, 2000));
    // 返回一个占位图片
    const placeholderImage = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAyNCIgaGVpZ2h0PSIxMDI0IiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHdpZHRoPSIxMDI0IiBoZWlnaHQ9IjEwMjQiIGZpbGw9IiNmMGYwZjAiLz48dGV4dCB4PSI1MTIiIHk9IjUxMiIgZm9udC1zaXplPSIyNCIgZmlsbD0iIzk5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7lm77niYfliqDovb3lpLHotKU8L3RleHQ+PC9zdmc+';
    return {
      imageUrl: '',
      imageData: placeholderImage
    };
  }
}

module.exports = new DoubaoService();

