// Additional script to fix dashboard UI issues

document.addEventListener('DOMContentLoaded', () => {
    // Fix sidebar navigation
    initSidebarNavigation();
    
    // Add additional comparison charts
    addComparisonCharts();
});

// Initialize sidebar navigation with proper section scrolling
function initSidebarNavigation() {
    const navLinks = document.querySelectorAll('.sidebar-nav a');
    const sections = {
        '#dashboard': document.querySelector('.dashboard-content'),
        '#github': document.getElementById('github-stats-section'),
        '#jira': document.getElementById('jira-stats-section'),
        '#settings': document.getElementById('status-card') // Fallback to status card for settings
    };
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Update active link
            document.querySelector('.sidebar-nav li.active')?.classList.remove('active');
            link.parentElement.classList.add('active');
            
            // Update page title
            const pageTitle = link.textContent.trim();
            document.getElementById('page-title').textContent = pageTitle;
            
            // Scroll to appropriate section
            const targetId = link.getAttribute('href');
            const targetSection = sections[targetId];
            
            if (targetSection) {
                targetSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

// Add additional comparison charts
function addComparisonCharts() {
    // Create container for comparison charts if it doesn't exist
    let comparisonSection = document.getElementById('comparison-charts-section');
    
    if (!comparisonSection) {
        comparisonSection = document.createElement('section');
        comparisonSection.id = 'comparison-charts-section';
        comparisonSection.className = 'dashboard-section';
        comparisonSection.style.display = 'none';
        
        const sectionTitle = document.createElement('h3');
        sectionTitle.className = 'section-title';
        sectionTitle.textContent = 'Performance Comparisons';
        comparisonSection.appendChild(sectionTitle);
        
        const chartsContainer = document.createElement('div');
        chartsContainer.className = 'comparison-chart-container';
        
        // Create first comparison chart - GitHub Activity
        const githubComparisonDiv = document.createElement('div');
        githubComparisonDiv.className = 'comparison-chart';
        const githubCanvas = document.createElement('canvas');
        githubCanvas.id = 'github-comparison-chart';
        githubComparisonDiv.appendChild(githubCanvas);
        
        // Create second comparison chart - Jira Activity
        const jiraComparisonDiv = document.createElement('div');
        jiraComparisonDiv.className = 'comparison-chart';
        const jiraCanvas = document.createElement('canvas');
        jiraCanvas.id = 'jira-comparison-chart';
        jiraComparisonDiv.appendChild(jiraCanvas);
        
        // Add charts to container
        chartsContainer.appendChild(githubComparisonDiv);
        chartsContainer.appendChild(jiraComparisonDiv);
        comparisonSection.appendChild(chartsContainer);
        
        // Add section after GitHub stats section
        const githubStatsSection = document.getElementById('github-stats-section');
        githubStatsSection.parentNode.insertBefore(comparisonSection, githubStatsSection.nextSibling);
    }
    
    // Hook into the existing updateDashboard function
    const originalUpdateDashboard = window.updateDashboard;
    
    if (originalUpdateDashboard) {
        window.updateDashboard = function(data) {
            // Call original function
            originalUpdateDashboard(data);
            
            // Update our comparison charts
            if (data && data.scores && data.scores.length > 0) {
                createComparisonCharts(data.scores);
                comparisonSection.style.display = 'block';
            } else {
                comparisonSection.style.display = 'none';
            }
        };
    }
}

// Create comparison charts
function createComparisonCharts(scores) {
    if (!scores || scores.length === 0) return;
    
    // Create GitHub activity comparison chart
    createGitHubComparisonChart(scores);
    
    // Create Jira activity comparison chart
    createJiraComparisonChart(scores);
}

// Create GitHub comparison chart
function createGitHubComparisonChart(scores) {
    const ctx = document.getElementById('github-comparison-chart').getContext('2d');
    const topEngineers = scores.slice(0, 5);
    
    // Prepare data
    const labels = topEngineers.map(score => score.engineer);
    const prsData = topEngineers.map(score => score.github_stats.prs_created);
    const commitsData = topEngineers.map(score => score.github_stats.commits_made);
    const reviewsData = topEngineers.map(score => score.github_stats.prs_reviewed);
    
    // Destroy existing chart if it exists
    if (window.githubComparisonChart) {
        window.githubComparisonChart.destroy();
    }
    
    // Create new chart
    window.githubComparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'PRs Created',
                    data: prsData,
                    backgroundColor: 'rgba(52, 152, 219, 0.7)',
                    borderColor: 'rgba(52, 152, 219, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Commits',
                    data: commitsData,
                    backgroundColor: 'rgba(46, 204, 113, 0.7)',
                    borderColor: 'rgba(46, 204, 113, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Reviews',
                    data: reviewsData,
                    backgroundColor: 'rgba(155, 89, 182, 0.7)',
                    borderColor: 'rgba(155, 89, 182, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'GitHub Activity Comparison'
                },
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Create Jira comparison chart
function createJiraComparisonChart(scores) {
    const ctx = document.getElementById('jira-comparison-chart').getContext('2d');
    const topEngineers = scores.slice(0, 5);
    
    // Prepare data
    const labels = topEngineers.map(score => score.engineer);
    const ticketsData = topEngineers.map(score => score.jira_stats.tickets_completed);
    const storyPointsData = topEngineers.map(score => score.jira_stats.story_points);
    
    // Destroy existing chart if it exists
    if (window.jiraComparisonChart) {
        window.jiraComparisonChart.destroy();
    }
    
    // Create new chart
    window.jiraComparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Tickets Completed',
                    data: ticketsData,
                    backgroundColor: 'rgba(230, 126, 34, 0.7)',
                    borderColor: 'rgba(230, 126, 34, 1)',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: 'Story Points',
                    data: storyPointsData,
                    backgroundColor: 'rgba(231, 76, 60, 0.7)',
                    borderColor: 'rgba(231, 76, 60, 1)',
                    borderWidth: 1,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Jira Activity Comparison'
                },
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Tickets'
                    }
                },
                y1: {
                    beginAtZero: true,
                    position: 'right',
                    grid: {
                        drawOnChartArea: false
                    },
                    title: {
                        display: true,
                        text: 'Story Points'
                    }
                }
            }
        }
    });
}