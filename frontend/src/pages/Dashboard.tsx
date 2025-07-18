import React from 'react'
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  Avatar,
} from '@mui/material'
import {
  Description as DocumentIcon,
  Search as SearchIcon,
  CloudUpload as UploadIcon,
  TrendingUp as TrendingIcon,
} from '@mui/icons-material'
import { useQuery } from 'react-query'
import { apiService } from '../services/api'
import { formatDistanceToNow } from 'date-fns'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

const Dashboard: React.FC = () => {
  const { data: stats, isLoading: statsLoading } = useQuery('stats', apiService.getStats)
  const { data: health, isLoading: healthLoading } = useQuery('health', apiService.getHealth)

  const entityDistribution = stats?.entity_distribution ? 
    Object.entries(stats.entity_distribution).map(([key, value]) => ({
      name: key,
      value: value as number
    })) : []

  const processingStats = [
    { label: 'Completed', value: stats?.processing_stats.completed || 0, color: '#4caf50' },
    { label: 'Processing', value: stats?.processing_stats.processing || 0, color: '#ff9800' },
    { label: 'Failed', value: stats?.processing_stats.failed || 0, color: '#f44336' },
  ]

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                  <DocumentIcon />
                </Avatar>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Total Documents
                  </Typography>
                  <Typography variant="h4">
                    {statsLoading ? '...' : stats?.total_documents || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ bgcolor: 'secondary.main', mr: 2 }}>
                  <SearchIcon />
                </Avatar>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Total Entities
                  </Typography>
                  <Typography variant="h4">
                    {statsLoading ? '...' : stats?.total_entities || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                  <UploadIcon />
                </Avatar>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Success Rate
                  </Typography>
                  <Typography variant="h4">
                    {statsLoading ? '...' : 
                      stats?.processing_stats.completed && stats?.processing_stats.completed > 0
                        ? Math.round((stats.processing_stats.completed / 
                            (stats.processing_stats.completed + stats.processing_stats.failed)) * 100)
                        : 0}%
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                  <TrendingIcon />
                </Avatar>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    System Status
                  </Typography>
                  <Chip 
                    label={healthLoading ? 'Checking...' : health?.status || 'Unknown'}
                    color={health?.status === 'healthy' ? 'success' : 'error'}
                    size="small"
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Processing Status
              </Typography>
              <Box sx={{ mt: 2 }}>
                {processingStats.map((stat) => (
                  <Box key={stat.label} sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">{stat.label}</Typography>
                      <Typography variant="body2">{stat.value}</Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={(stat.value / Math.max(...processingStats.map(s => s.value))) * 100}
                      sx={{ 
                        height: 8, 
                        borderRadius: 4,
                        backgroundColor: 'grey.200',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: stat.color,
                        }
                      }}
                    />
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Entity Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={entityDistribution}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {entityDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recent Uploads
          </Typography>
          {statsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <LinearProgress sx={{ width: '50%' }} />
            </Box>
          ) : stats?.recent_uploads && stats.recent_uploads.length > 0 ? (
            <Grid container spacing={2}>
              {stats.recent_uploads.slice(0, 6).map((doc) => (
                <Grid item xs={12} sm={6} md={4} key={doc.id}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle2" noWrap>
                        {doc.filename}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        {formatDistanceToNow(new Date(doc.uploaded_at), { addSuffix: true })}
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        <Chip 
                          label={doc.status} 
                          size="small"
                          color={doc.status === 'completed' ? 'success' : 
                                 doc.status === 'processing' ? 'warning' : 'error'}
                        />
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          {doc.entity_count} entities found
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Typography variant="body2" color="textSecondary" sx={{ textAlign: 'center', py: 4 }}>
              No recent uploads
            </Typography>
          )}
        </CardContent>
      </Card>
    </Box>
  )
}

export default Dashboard 