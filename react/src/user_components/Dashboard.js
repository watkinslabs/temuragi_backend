import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import config from '../config';

const Dashboard = () => {
    const { user } = useAuth();
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch_dashboard_data();
    }, []);

    const fetch_dashboard_data = async () => {
        try {
            // You can customize this endpoint
            const response = await fetch(config.getUrl('/dashboard/stats'), {
                headers: config.getAuthHeaders()
            });
            
            if (response.ok) {
                const data = await response.json();
                setStats(data);
            }
        } catch (error) {
            console.error('Failed to fetch dashboard data:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="dashboard">
            <div className="container-fluid">
                <div className="row mb-4">
                    <div className="col">
                        <h2>Welcome back{user?.name ? `, ${user.name}` : ''}!</h2>
                        <p className="text-muted">Here's what's happening with your account today.</p>
                    </div>
                </div>

                {loading ? (
                    <div className="d-flex justify-content-center p-5">
                        <div className="spinner-border text-primary" role="status">
                            <span className="visually-hidden">Loading...</span>
                        </div>
                    </div>
                ) : (
                    <div className="row">
                        {/* Stats Cards */}
                        <div className="col-lg-3 col-md-6 mb-4">
                            <div className="card border-0 shadow-sm">
                                <div className="card-body">
                                    <div className="d-flex justify-content-between align-items-center">
                                        <div>
                                            <h6 className="text-muted mb-2">Total Items</h6>
                                            <h3 className="mb-0">{stats?.total_items || 0}</h3>
                                        </div>
                                        <div className="text-primary">
                                            <i className="fas fa-box fa-2x opacity-50"></i>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="col-lg-3 col-md-6 mb-4">
                            <div className="card border-0 shadow-sm">
                                <div className="card-body">
                                    <div className="d-flex justify-content-between align-items-center">
                                        <div>
                                            <h6 className="text-muted mb-2">Active Tasks</h6>
                                            <h3 className="mb-0">{stats?.active_tasks || 0}</h3>
                                        </div>
                                        <div className="text-success">
                                            <i className="fas fa-tasks fa-2x opacity-50"></i>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="col-lg-3 col-md-6 mb-4">
                            <div className="card border-0 shadow-sm">
                                <div className="card-body">
                                    <div className="d-flex justify-content-between align-items-center">
                                        <div>
                                            <h6 className="text-muted mb-2">Messages</h6>
                                            <h3 className="mb-0">{stats?.messages || 0}</h3>
                                        </div>
                                        <div className="text-info">
                                            <i className="fas fa-envelope fa-2x opacity-50"></i>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="col-lg-3 col-md-6 mb-4">
                            <div className="card border-0 shadow-sm">
                                <div className="card-body">
                                    <div className="d-flex justify-content-between align-items-center">
                                        <div>
                                            <h6 className="text-muted mb-2">Notifications</h6>
                                            <h3 className="mb-0">{stats?.notifications || 0}</h3>
                                        </div>
                                        <div className="text-warning">
                                            <i className="fas fa-bell fa-2x opacity-50"></i>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Quick Actions */}
                <div className="row mt-4">
                    <div className="col-12">
                        <div className="card border-0 shadow-sm">
                            <div className="card-header bg-transparent">
                                <h5 className="mb-0">Quick Actions</h5>
                            </div>
                            <div className="card-body">
                                <div className="d-flex flex-wrap gap-2">
                                    <button className="btn btn-primary">
                                        <i className="fas fa-plus me-2"></i>Create New
                                    </button>
                                    <button className="btn btn-outline-secondary">
                                        <i className="fas fa-file-export me-2"></i>Export Data
                                    </button>
                                    <button className="btn btn-outline-secondary">
                                        <i className="fas fa-cog me-2"></i>Settings
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Recent Activity */}
                <div className="row mt-4">
                    <div className="col-12">
                        <div className="card border-0 shadow-sm">
                            <div className="card-header bg-transparent">
                                <h5 className="mb-0">Recent Activity</h5>
                            </div>
                            <div className="card-body">
                                <p className="text-muted">No recent activity to display.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};


// Make sure window.Components exists
if (!window.Components) {
    window.Components = {};
}

// Register the component
window.Components.Dashboard = Dashboard;

// Also export normally
export default Dashboard;