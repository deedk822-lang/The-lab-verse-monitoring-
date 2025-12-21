import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Users, DollarSign, TrendingUp, Calendar, Send, CheckCircle, AlertCircle, Clock } from 'lucide-react';

const VaalDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [clients, setClients] = useState([]);
  const [revenueData, setRevenueData] = useState([]);
  const [sovereignStatus, setSovereignStatus] = useState({});

  const activateSovereignMode = async (department) => {
    setSovereignStatus(prev => ({ ...prev, [department]: 'INITIATING...' }));

    try {
        const signal = "Current SABC Trend: Youth Digital Skills Gap";

        const response = await fetch('/api/empire/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                signal: signal,
                department: department
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            setSovereignStatus(prev => ({ ...prev, [department]: 'REVENUE ACTIVE' }));
            alert(`Empire Action Complete!\nProduct Live: ${data.link}`);
        } else {
            throw new Error(data.message);
        }

    } catch (e) {
        console.error(e);
        setSovereignStatus(prev => ({ ...prev, [department]: 'ERROR' }));
    }
  }

  useEffect(() => {
    fetch('/api/dashboard')
      .then(res => res.json())
      .then(data => {
        const clientData = data.clients.map(c => ({
          id: c.id,
          name: c.name,
          type: c.business_type,
          revenue: c.subscription_amount,
          status: c.active ? 'active' : 'inactive',
          posts: 0 // Placeholder
        }));
        setClients(clientData);

        const dailyRevenue = {};
        data.revenue.forEach(r => {
          const date = new Date(r.payment_date).toLocaleDateString('en-US', { weekday: 'short' });
          if (!dailyRevenue[date]) {
            dailyRevenue[date] = { date, revenue: 0, clients: new Set() };
          }
          dailyRevenue[date].revenue += r.amount;
          dailyRevenue[date].clients.add(r.client_id);
        });

        const revenueChartData = Object.values(dailyRevenue).map(d => ({
          ...d,
          clients: d.clients.size
        }));
        setRevenueData(revenueChartData);
      });
  }, []);

  const totalRevenue = clients.reduce((sum, c) => sum + c.revenue, 0);
  const activeClients = clients.filter(c => c.status === 'active').length;
  const totalPosts = clients.reduce((sum, c) => sum + c.posts, 0);
  const monthlyProjection = totalRevenue * 4;

  const serviceBreakdown = [
    { name: 'Social Media', value: 1800, color: '#3b82f6' },
    { name: 'Websites', value: 2500, color: '#10b981' },
    { name: 'WhatsApp Bots', value: 0, color: '#f59e0b' }
  ];

  const upcomingTasks = [
    { id: 1, client: 'Smit Butchery', task: 'Generate weekly content', time: '2h', priority: 'high' },
    { id: 2, client: 'Vaal Motors', task: 'Schedule 10 posts', time: '4h', priority: 'medium' },
    { id: 3, client: 'Koffie & More', task: 'Send invoice', time: '1d', priority: 'low' }
  ];

  const StatCard = ({ icon: Icon, title, value, subtitle, color }) => (
    <div className="bg-white rounded-lg shadow p-6 border-l-4" style={{ borderColor: color }}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-3xl font-bold mt-2">{value}</p>
          {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <Icon className="w-12 h-12 opacity-20" style={{ color }} />
      </div>
    </div>
  );

  const ClientRow = ({ client }) => (
    <tr className="hover:bg-gray-50">
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center">
          <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
            {client.name.charAt(0)}
          </div>
          <div className="ml-4">
            <div className="text-sm font-medium text-gray-900">{client.name}</div>
            <div className="text-sm text-gray-500">{client.type}</div>
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
          {client.status}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        R{client.revenue.toLocaleString()}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        {client.posts} posts
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
        <button className="text-blue-600 hover:text-blue-900 mr-3">View</button>
        <button className="text-green-600 hover:text-green-900">Generate</button>
      </td>
    </tr>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Vaal AI Empire</h1>
              <p className="text-sm text-gray-600 mt-1">Production Dashboard</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm text-gray-600">Monthly Target</p>
                <p className="text-lg font-bold text-blue-600">
                  R{monthlyProjection.toLocaleString()} / R25,000
                </p>
              </div>
              <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center">
                <TrendingUp className="w-8 h-8 text-blue-600" />
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {['overview', 'clients', 'revenue', 'automation', 'sovereign'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm capitalize`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard
                icon={DollarSign}
                title="Weekly Revenue"
                value={`R${totalRevenue.toLocaleString()}`}
                subtitle={`${((monthlyProjection / 25000) * 100).toFixed(0)}% of monthly target`}
                color="#10b981"
              />
              <StatCard
                icon={Users}
                title="Active Clients"
                value={activeClients}
                subtitle="All paying subscribers"
                color="#3b82f6"
              />
              <StatCard
                icon={Send}
                title="Posts Generated"
                value={totalPosts}
                subtitle="This week"
                color="#f59e0b"
              />
              <StatCard
                icon={Calendar}
                title="Next Delivery"
                value="Monday"
                subtitle="6:00 AM automated"
                color="#8b5cf6"
              />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Revenue Chart */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">Weekly Revenue</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={revenueData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="revenue" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Service Breakdown */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">Revenue by Service</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={serviceBreakdown}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={entry => `R${entry.value}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {serviceBreakdown.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Upcoming Tasks */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Upcoming Tasks</h3>
              <div className="space-y-3">
                {upcomingTasks.map(task => (
                  <div key={task.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Clock className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="font-medium">{task.task}</p>
                        <p className="text-sm text-gray-600">{task.client}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-gray-600">{task.time}</span>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        task.priority === 'high' ? 'bg-red-100 text-red-800' :
                        task.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {task.priority}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'clients' && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-lg font-semibold">Active Clients</h3>
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                + Add Client
              </button>
            </div>
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Client
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Monthly Revenue
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Content
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {clients.map(client => (
                  <ClientRow key={client.id} client={client} />
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'revenue' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h4 className="text-sm text-gray-600 mb-2">This Week</h4>
                <p className="text-3xl font-bold text-gray-900">R{totalRevenue.toLocaleString()}</p>
                <p className="text-sm text-green-600 mt-2">↑ 100% vs last week</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <h4 className="text-sm text-gray-600 mb-2">Projected Monthly</h4>
                <p className="text-3xl font-bold text-gray-900">R{monthlyProjection.toLocaleString()}</p>
                <p className="text-sm text-blue-600 mt-2">{((monthlyProjection / 25000) * 100).toFixed(0)}% of R25k target</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <h4 className="text-sm text-gray-600 mb-2">Avg per Client</h4>
                <p className="text-3xl font-bold text-gray-900">
                  R{Math.round(totalRevenue / activeClients).toLocaleString()}
                </p>
                <p className="text-sm text-gray-600 mt-2">Per month</p>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Revenue Trend</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={revenueData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {activeTab === 'automation' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Automation Status</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                    <div>
                      <p className="font-medium">Content Generation</p>
                      <p className="text-sm text-gray-600">Runs every Monday at 6:00 AM</p>
                    </div>
                  </div>
                  <span className="text-sm text-green-600 font-medium">Active</span>
                </div>
                <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                    <div>
                      <p className="font-medium">Social Media Posting</p>
                      <p className="text-sm text-gray-600">Runs daily at 9:00 AM</p>
                    </div>
                  </div>
                  <span className="text-sm text-green-600 font-medium">Active</span>
                </div>
                <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                    <div>
                      <p className="font-medium">Daily Reports</p>
                      <p className="text-sm text-gray-600">Runs daily at 6:00 PM</p>
                    </div>
                  </div>
                  <span className="text-sm text-green-600 font-medium">Active</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Manual Actions</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button className="p-4 border-2 border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 font-medium">
                  Generate Content Now
                </button>
                <button className="p-4 border-2 border-green-600 text-green-600 rounded-lg hover:bg-green-50 font-medium">
                  Post Scheduled Content
                </button>
                <button className="p-4 border-2 border-purple-600 text-purple-600 rounded-lg hover:bg-purple-50 font-medium">
                  Send Revenue Report
                </button>
                <button className="p-4 border-2 border-orange-600 text-orange-600 rounded-lg hover:bg-orange-50 font-medium">
                  Backup Database
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'sovereign' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Sovereign Protocol</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {['Education', 'Finance', 'Security'].map(dept => (
                <div key={dept} className="border p-4 rounded-lg">
                  <h4 className="font-bold text-xl mb-2">{dept}</h4>
                  <p className="text-sm text-gray-600 mb-4">
                    Activate the full agent-to-revenue cycle for this department.
                  </p>
                  <button
                    onClick={() => activateSovereignMode(dept)}
                    className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400"
                    disabled={sovereignStatus[dept] === 'INITIATING...'}
                  >
                    Activate {dept}
                  </button>
                  <p className="text-center mt-2 text-sm font-medium">
                    Status: <span
                      className={
                        sovereignStatus[dept] === 'REVENUE ACTIVE' ? 'text-green-500' :
                        sovereignStatus[dept] === 'ERROR' ? 'text-red-500' :
                        'text-yellow-500'
                      }
                    >
                      {sovereignStatus[dept] || 'Idle'}
                    </span>
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default VaalDashboard;
