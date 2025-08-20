import React, { useState, useRef } from 'react';
import { chatAPI } from '../../utils/api';
import './PDFUpload.css';

const PDFUpload = () => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelect = (files) => {
    const pdfFiles = Array.from(files).filter(file => file.type === 'application/pdf');
    if (pdfFiles.length !== files.length) {
      setUploadStatus({
        type: 'error',
        message: 'Only PDF files are allowed'
      });
      return;
    }
    setSelectedFiles(prev => [...prev, ...pdfFiles]);
    setUploadStatus(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleFileInputChange = (e) => {
    handleFileSelect(e.target.files);
  };

  const removeFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const clearFiles = () => {
    setSelectedFiles([]);
    setUploadStatus(null);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    setUploading(true);
    setUploadStatus({ type: 'loading', message: 'Processing PDF files...' });

    try {
      const response = await chatAPI.uploadPDF(selectedFiles);
      setUploadStatus({
        type: 'success',
        message: `Successfully processed ${response.data.chunks_count} text chunks. You can now ask questions about your documents!`
      });
      setSelectedFiles([]);
    } catch (error) {
      setUploadStatus({
        type: 'error',
        message: error.response?.data?.detail || 'Failed to upload PDF files'
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-container">
      <h2 className="upload-title">Upload PDF Documents</h2>
      <p className="upload-subtitle">
        Upload your PDF files to start asking questions about their content
      </p>

      <div
        className={`upload-dropzone ${dragOver ? 'dragover' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
      >
        <div className="upload-icon">📄</div>
        <div className="upload-text">
          Drop PDF files here or click to browse
        </div>
        <div className="upload-hint">
          Supports multiple PDF files
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf"
        onChange={handleFileInputChange}
        className="file-input"
      />

      {selectedFiles.length > 0 && (
        <div className="selected-files">
          <div className="file-list">
            {selectedFiles.map((file, index) => (
              <div key={index} className="file-item">
                <div>
                  <div className="file-name">{file.name}</div>
                  <div className="file-size">{formatFileSize(file.size)}</div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(index);
                  }}
                  className="remove-file"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
          
          <div>
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="upload-button"
            >
              {uploading ? 'Processing...' : 'Upload & Process'}
            </button>
            <button
              onClick={clearFiles}
              disabled={uploading}
              className="clear-button"
            >
              Clear All
            </button>
          </div>
        </div>
      )}

      {uploadStatus && (
        <div className={`upload-status ${uploadStatus.type}`}>
          {uploadStatus.message}
        </div>
      )}
    </div>
  );
};

export default PDFUpload;
