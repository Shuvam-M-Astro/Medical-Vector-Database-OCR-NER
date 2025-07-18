import React, { useState, useCallback } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Alert,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material'
import {
  CloudUpload as UploadIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Description as FileIcon,
} from '@mui/icons-material'
import { useDropzone } from 'react-dropzone'
import { useMutation, useQueryClient } from 'react-query'
import { apiService } from '../services/api'
import toast from 'react-hot-toast'
import { UploadProgress } from '../types'

const Upload: React.FC = () => {
  const [uploadProgress, setUploadProgress] = useState<UploadProgress[]>([])
  const [metadata, setMetadata] = useState({
    documentType: '',
    department: '',
    tags: '',
  })
  
  const queryClient = useQueryClient()

  const uploadMutation = useMutation(
    (files: File[]) => apiService.batchUpload(files),
    {
      onSuccess: (data) => {
        toast.success(`Successfully uploaded ${data.length} documents`)
        queryClient.invalidateQueries('stats')
        queryClient.invalidateQueries('documents')
        setUploadProgress([])
      },
      onError: (error: any) => {
        toast.error(`Upload failed: ${error.response?.data?.detail || error.message}`)
      },
    }
  )

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newProgress: UploadProgress[] = acceptedFiles.map(file => ({
      filename: file.name,
      progress: 0,
      status: 'uploading',
    }))
    
    setUploadProgress(newProgress)
    
    // Simulate upload progress
    acceptedFiles.forEach((file, index) => {
      const interval = setInterval(() => {
        setUploadProgress(prev => 
          prev.map((item, i) => 
            i === index && item.progress < 90
              ? { ...item, progress: item.progress + 10 }
              : item
          )
        )
      }, 200)

      setTimeout(() => {
        clearInterval(interval)
        setUploadProgress(prev => 
          prev.map((item, i) => 
            i === index ? { ...item, progress: 100, status: 'processing' } : item
          )
        )
      }, 2000)
    })

    // Start actual upload
    uploadMutation.mutate(acceptedFiles)
  }, [uploadMutation])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.jpg', '.jpeg', '.png', '.tiff', '.bmp'],
    },
    multiple: true,
  })

  const handleMetadataChange = (field: string, value: string) => {
    setMetadata(prev => ({ ...prev, [field]: value }))
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Upload Documents
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Upload Medical Documents
              </Typography>
              
              <Box
                {...getRootProps()}
                sx={{
                  border: '2px dashed',
                  borderColor: isDragActive ? 'primary.main' : 'grey.300',
                  borderRadius: 2,
                  p: 4,
                  textAlign: 'center',
                  cursor: 'pointer',
                  backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    borderColor: 'primary.main',
                    backgroundColor: 'action.hover',
                  },
                }}
              >
                <input {...getInputProps()} />
                <UploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  or click to select files
                </Typography>
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  Supported formats: PDF, JPG, PNG, TIFF, BMP
                </Typography>
              </Box>

              {uploadProgress.length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Upload Progress
                  </Typography>
                  <List>
                    {uploadProgress.map((item, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          {item.status === 'completed' ? (
                            <SuccessIcon color="success" />
                          ) : item.status === 'failed' ? (
                            <ErrorIcon color="error" />
                          ) : (
                            <FileIcon />
                          )}
                        </ListItemIcon>
                        <ListItemText
                          primary={item.filename}
                          secondary={
                            <Box>
                              <LinearProgress 
                                variant="determinate" 
                                value={item.progress} 
                                sx={{ mb: 1 }}
                              />
                              <Chip 
                                label={item.status} 
                                size="small"
                                color={
                                  item.status === 'completed' ? 'success' :
                                  item.status === 'failed' ? 'error' :
                                  item.status === 'processing' ? 'warning' : 'default'
                                }
                              />
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {uploadMutation.isError && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  Upload failed. Please try again.
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Document Metadata
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Document Type</InputLabel>
                <Select
                  value={metadata.documentType}
                  label="Document Type"
                  onChange={(e) => handleMetadataChange('documentType', e.target.value)}
                >
                  <MenuItem value="medical_report">Medical Report</MenuItem>
                  <MenuItem value="lab_result">Lab Result</MenuItem>
                  <MenuItem value="prescription">Prescription</MenuItem>
                  <MenuItem value="imaging">Imaging</MenuItem>
                  <MenuItem value="consent_form">Consent Form</MenuItem>
                  <MenuItem value="other">Other</MenuItem>
                </Select>
              </FormControl>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Department</InputLabel>
                <Select
                  value={metadata.department}
                  label="Department"
                  onChange={(e) => handleMetadataChange('department', e.target.value)}
                >
                  <MenuItem value="cardiology">Cardiology</MenuItem>
                  <MenuItem value="neurology">Neurology</MenuItem>
                  <MenuItem value="oncology">Oncology</MenuItem>
                  <MenuItem value="radiology">Radiology</MenuItem>
                  <MenuItem value="emergency">Emergency</MenuItem>
                  <MenuItem value="general">General</MenuItem>
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Tags"
                value={metadata.tags}
                onChange={(e) => handleMetadataChange('tags', e.target.value)}
                placeholder="Enter tags separated by commas"
                helperText="Optional: Add tags to help with organization"
              />
            </CardContent>
          </Card>

          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Upload Guidelines
              </Typography>
              <Typography variant="body2" color="textSecondary" paragraph>
                • Maximum file size: 50MB per file
              </Typography>
              <Typography variant="body2" color="textSecondary" paragraph>
                • Supported formats: PDF, JPG, PNG, TIFF, BMP
              </Typography>
              <Typography variant="body2" color="textSecondary" paragraph>
                • Documents will be processed for OCR and NER extraction
              </Typography>
              <Typography variant="body2" color="textSecondary">
                • Processing time varies based on document size and complexity
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Upload 