import React, { useState, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { csvAPI } from '../../utils/api';
import './CSVUpload.css';

const CSVUpload = () => {
  const { user } = useAuth();
  const [selectedFile, setSelectedFile] = useState(null);
  const [tableName, setTableName] = useState('claims_list');
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const isAdmin = user?.role === 'ADMIN';

  if (!isAdmin) {
    return (
      <div className="csv-upload-container">
        <div className="access-denied">
          <h2>Admin Access Required</h2>
          <p>Only administrators can upload CSV files to the database.</p>
          <p>Your current role: <strong>{user?.role || 'USER'}</strong></p>
        </div>
      </div>
    );
  }

  const handleFileSelect = (files) => {
    const file = files[0];
    if (!file) return;
    
    if (!file.name.endsWith('.csv')) {
      setUploadStatus({
        type: 'error',
        message: 'Only CSV files are allowed'
      });
      return;
    }
    
    setSelectedFile(file);
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

  const clearFile = () => {
    setSelectedFile(null);
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
    if (!selectedFile) return;

    setUploading(true);
    setUploadStatus({ type: 'loading', message: 'Uploading CSV file...' });

    try {
      const response = await csvAPI.upload(selectedFile, tableName);
      setUploadStatus({
        type: 'success',
        message: response.data.message
      });
      setSelectedFile(null);
    } catch (error) {
      if (error.response?.status === 429 || error.response?.data?.detail?.includes('quota')) {
        setUploadStatus({
          type: 'error',
          message: 'Out of Message Quota - Please try again later'
        });
      } else {
        setUploadStatus({
          type: 'error',
          message: error.response?.data?.detail || 'Failed to upload CSV file'
        });
      }
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="csv-upload-container">
      <h2 className="upload-title">Upload Claims CSV Data</h2>
      <p className="upload-subtitle">
        Upload CSV files to populate the claims database tables (Admin only)
      </p>

      <div className="table-selector">
        <label htmlFor="tableName">Target Table:</label>
        <select
          id="tableName"
          value={tableName}
          onChange={(e) => setTableName(e.target.value)}
          className="table-select"
          disabled={uploading}
        >
          <option value="claims_list">Claims List</option>
          <option value="claims_detail">Claims Detail</option>
        </select>
      </div>

      <div
        className={`upload-dropzone ${dragOver ? 'dragover' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
      >
        <div className="upload-icon">📊</div>
        <div className="upload-text">
          Drop CSV file here or click to browse
        </div>
        <div className="upload-hint">
          Supports pipe-delimited CSV files (|)
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".csv"
        onChange={handleFileInputChange}
        className="file-input"
      />

      {selectedFile && (
        <div className="selected-file">
          <div className="file-info">
            <div className="file-name">{selectedFile.name}</div>
            <div className="file-size">{formatFileSize(selectedFile.size)}</div>
          </div>
          <button
            onClick={clearFile}
            disabled={uploading}
            className="remove-file"
          >
            Remove
          </button>
        </div>
      )}

      {selectedFile && (
        <div className="upload-actions">
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="upload-button"
          >
            {uploading ? 'Uploading...' : `Upload to ${tableName}`}
          </button>
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

export default CSVUpload;
