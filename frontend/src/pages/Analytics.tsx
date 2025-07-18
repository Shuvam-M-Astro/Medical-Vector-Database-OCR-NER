import React from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
} from '@mui/material'
import { useQuery } from 'react-query'
import { apiService } from '../services/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

const Analytics: React.FC = () => {
  const { data: stats, isLoading } = useQuery('stats', apiService.getStats)

  const entityDistribution = stats?.entity_distribution ? 
    Object.entries(stats.entity_distribution).map(([key, value]) => ({
      name: key,
      value: value as number
    })) : []

  const processingData = [
    { name: 'Completed', value: stats?.processing_stats.completed || 0 },
    { name: 'Processing', value: stats?.processing_stats.processing || 0 },
    { name: 'Failed', value: stats?.processing_stats.failed || 0 },
  ]

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Analytics & Insights
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Processing Statistics
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={processingData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Entity Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
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

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Overview
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Typography variant="h4" color="primary">
                    {stats?.total_documents || 0}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Total Documents
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Typography variant="h4" color="secondary">
                    {stats?.total_entities || 0}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Total Entities
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Typography variant="h4" color="success.main">
                    {stats?.processing_stats.completed || 0}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Completed
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Typography variant="h4" color="error.main">
                    {stats?.processing_stats.failed || 0}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Failed
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Analytics 