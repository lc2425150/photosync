import { api } from './client'

export const notificationsApi = {
  list: () => api.get('/notification-configs'),
  create: (data) => api.post('/notification-configs', data),
  update: (id, data) => api.put(`/notification-configs/${id}`, data),
  delete: (id) => api.delete(`/notification-configs/${id}`),
  test: (id) => api.post(`/notification-configs/test?cid=${id}`),
}
