// DOM Elements
const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebar = document.querySelector('.sidebar');
const runAnalysisBtn = document.getElementById('run-analysis');
const startDateInput = document.getElementById('start-date');
const endDateInput = document.getElementById('end-date');
const loadingOverlay = document.getElementById('loading-overlay');
const statusCard = document.getElementById('status-card');
const summarySection = document.getElementById('summary-section');
const contributorsSection = document.getElementById('contributors-section');
const executiveSummarySection = document.getElementById('executive-summary-section');
const githubStatsSection = document.getElementById('github-stats-section');
const jiraStatsSection = document.getElementById('jira-stats-section');
const championSection = document.getElementById('champion-section');
const performanceGraphsSection = document.getElementById('performance-graphs-section');
const activityHeatmapSection = document.getElementById('activity-heatmap-section');

// Chart objects
let scoreDistributionChart = null;
let githubJiraChart = null;

// Dashboard Elements
const engineersCount = document.getElementById('engineers-count');
const avgTeamScore = document.getElementById('avg-team-score');
const topPerformer = document.getElementById('top-performer');
const contributorsTableBody = document.getElementById('contributors-table-body');
const executiveSummaryPanel = document.getElementById('executive-summary-panel');
const totalPRs = document.getElementById('total-prs');
const totalCommits = document.getElementById('total-commits');
const totalReviews = document.getElementById('total-reviews');
const totalIssues = document.getElementById('total-issues');
const completedIssues = document.getElementById('completed-issues');
const championName = document.getElementById('champion-name');

// Initialize the dashboard
function initDashboard() {
    // Set default dates (today and 7 days ago)
    const today = new Date();
    const weekAgo = new Date();
    weekAgo.setDate(today.getDate() - 7);
    
    endDateInput.valueAsDate = today;
    startDateInput.valueAsDate = weekAgo;
    
    // Add event listeners
    sidebarToggle.addEventListener('click', toggleSidebar);
    runAnalysisBtn.addEventListener('click', runAnalysis);
    
    // Initialize navigation
    initNavigation();
}

// Toggle sidebar
function toggleSidebar() {
    sidebar.classList.toggle('collapsed');
}

// Initialize navigation
function initNavigation() {
    const navLinks = document.querySelectorAll('.sidebar-nav a');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Update active link
            document.querySelector('.sidebar-nav li.active').classList.remove('active');
            link.parentElement.classList.add('active');
            
            // Update page title
            const pageTitle = link.textContent.trim();
            document.getElementById('page-title').textContent = pageTitle;
        });
    });
}

// Run productivity analysis
async function runAnalysis() {
    const startDate = startDateInput.value;
    const endDate = endDateInput.value;
    
    if (!startDate || !endDate) {
        updateStatusCard('error', 'Please select both start and end dates');
        return;
    }
    
    console.log('Running analysis for period:', startDate, 'to', endDate);
    updateStatusCard('running', 'Running productivity analysis...');
    
    // Show loading overlay
    loadingOverlay.style.display = 'flex';
    
    try {
        // Make API call to backend
        const response = await fetch('/api/productivity/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                start_date: startDate,
                end_date: endDate
            })
        });
        
        if (!response.ok) {
            const responseText = await response.text();
            throw new Error(`API error: ${response.status} - ${responseText.substring(0, 100)}`);
        }
        
        // Only try to parse JSON if the response is OK
        const data = await response.json();
        
        // Update dashboard with results
        updateDashboard(data);
        
    } catch (error) {
        console.error('Analysis failed:', error);
        updateStatusCard('error', `Analysis failed: ${error.message}`);
    } finally {
        // Hide loading overlay
        loadingOverlay.style.display = 'none';
    }
}

// Update status card
function updateStatusCard(status, message) {
    const statusIcon = statusCard.querySelector('.status-icon i');
    const statusTitle = statusCard.querySelector('.status-text h3');
    const statusMessage = statusCard.querySelector('.status-text p');
    
    if (status === 'success') {
        statusIcon.className = 'fas fa-check-circle';
        statusIcon.style.color = 'var(--secondary-color)';
    } else if (status === 'error') {
        statusIcon.className = 'fas fa-exclamation-circle';
        statusIcon.style.color = 'var(--accent-color)';
    } else if (status === 'running') {
        statusIcon.className = 'fas fa-spinner fa-spin';
        statusIcon.style.color = 'var(--primary-color)';
    } else {
        statusIcon.className = 'fas fa-info-circle';
        statusIcon.style.color = 'var(--primary-color)';
    }
    
    statusTitle.textContent = status === 'success' ? 'Analysis Complete' : 
                             status === 'error' ? 'Error' : 
                             status === 'running' ? 'Running Analysis' : 'Ready';
    
    statusMessage.textContent = message || '';
}

// Update dashboard with analysis results
function updateDashboard(data) {
    if (!data || !data.scores || data.scores.length === 0) {
        updateStatusCard('error', 'No productivity data found for the specified period');
        hideAllSections();
        return;
    }
    
    updateStatusCard('success', `Analysis completed for period: ${data.period}`);
    
    // Update summary stats
    engineersCount.textContent = data.scores.length;
    
    const totalScore = data.scores.reduce((sum, score) => sum + score.total_score, 0);
    avgTeamScore.textContent = (totalScore / data.scores.length).toFixed(1);
    
    const topScore = data.scores[0];
    topPerformer.textContent = `${topScore.engineer} (${topScore.total_score.toFixed(1)})`;
    
    // Update contributors table
    updateContributorsTable(data.scores);
    
    // Update executive summary
    if (data.summary && data.summary.executive_summary) {
        executiveSummaryPanel.textContent = data.summary.executive_summary;
        executiveSummarySection.style.display = 'block';
    } else {
        executiveSummarySection.style.display = 'none';
    }
    
    // Update GitHub stats
    if (data.github_data) {
        totalPRs.textContent = data.github_data.total_prs;
        totalCommits.textContent = data.github_data.total_commits;
        totalReviews.textContent = data.github_data.total_reviews;
        githubStatsSection.style.display = 'block';
    } else {
        githubStatsSection.style.display = 'none';
    }
    
    // Update Jira stats
    if (data.jira_data) {
        totalIssues.textContent = data.jira_data.total_issues;
        completedIssues.textContent = data.jira_data.completed_issues;
        jiraStatsSection.style.display = 'block';
    } else {
        jiraStatsSection.style.display = 'none';
    }
    
    // Update champion banner
    if (data.scores.length > 0) {
        championName.textContent = data.scores[0].engineer;
        championSection.style.display = 'block';
    } else {
        championSection.style.display = 'none';
    }
    
    // Create and update performance graphs
    createPerformanceGraphs(data.scores);
    
    // Create activity heatmap
    createActivityHeatmap(data.scores);
    
    // Show all sections
    summarySection.style.display = 'block';
    contributorsSection.style.display = 'block';
}

// Update contributors table
function updateContributorsTable(scores) {
    contributorsTableBody.innerHTML = '';
    
    scores.slice(0, 10).forEach((score, index) => {
        const row = document.createElement('tr');
        
        // Determine rank symbol
        let rankSymbol = `#${index + 1}`;
        if (index === 0) rankSymbol = '#1 (Top)';
        else if (index === 1) rankSymbol = '#2';
        else if (index === 2) rankSymbol = '#3';
        
        row.innerHTML = `
            <td>${rankSymbol}</td>
            <td>${score.engineer}</td>
            <td>${score.total_score.toFixed(1)}</td>
            <td>${score.github_score.toFixed(1)}</td>
            <td>${score.jira_score.toFixed(1)}</td>
            <td>${score.quality_score.toFixed(1)}</td>
            <td>${score.collaboration_score.toFixed(1)}</td>
        `;
        
        contributorsTableBody.appendChild(row);
    });
}

// Hide all dashboard sections
function hideAllSections() {
    summarySection.style.display = 'none';
    contributorsSection.style.display = 'none';
    executiveSummarySection.style.display = 'none';
    githubStatsSection.style.display = 'none';
    jiraStatsSection.style.display = 'none';
    championSection.style.display = 'none';
    performanceGraphsSection.style.display = 'none';
    activityHeatmapSection.style.display = 'none';
}

// Create performance graphs
function createPerformanceGraphs(scores) {
    if (!scores || scores.length === 0) return;
    
    // Prepare data for score distribution chart
    const engineers = scores.map(score => score.engineer);
    const totalScores = scores.map(score => score.total_score);
    const githubScores = scores.map(score => score.github_score);
    const jiraScores = scores.map(score => score.jira_score);
    const qualityScores = scores.map(score => score.quality_score);
    const collaborationScores = scores.map(score => score.collaboration_score);
    
    // Create score distribution chart
    const scoreDistributionCtx = document.getElementById('score-distribution-chart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (scoreDistributionChart) {
        scoreDistributionChart.destroy();
    }
    
    scoreDistributionChart = new Chart(scoreDistributionCtx, {
        type: 'bar',
        data: {
            labels: engineers,
            datasets: [
                {
                    label: 'Total Score',
                    data: totalScores,
                    backgroundColor: 'rgba(52, 152, 219, 0.7)',
                    borderColor: 'rgba(52, 152, 219, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Engineer Performance Scores'
                },
                legend: {
                    display: false
                }
            }
        }
    });
    
    // Create GitHub vs Jira performance chart
    const githubJiraCtx = document.getElementById('github-jira-chart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (githubJiraChart) {
        githubJiraChart.destroy();
    }
    
    githubJiraChart = new Chart(githubJiraCtx, {
        type: 'radar',
        data: {
            labels: ['GitHub', 'Jira', 'Quality', 'Collaboration'],
            datasets: scores.slice(0, 3).map((score, index) => {
                const colors = [
                    'rgba(52, 152, 219, 0.7)',  // Blue
                    'rgba(46, 204, 113, 0.7)',  // Green
                    'rgba(155, 89, 182, 0.7)'   // Purple
                ];
                
                return {
                    label: score.engineer,
                    data: [
                        score.github_score,
                        score.jira_score,
                        score.quality_score,
                        score.collaboration_score
                    ],
                    backgroundColor: colors[index],
                    borderColor: colors[index].replace('0.7', '1'),
                    borderWidth: 1
                };
            })
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: {
                        display: true
                    },
                    suggestedMin: 0,
                    suggestedMax: 100,
                    ticks: {
                        display: false
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Top 3 Engineers'
                },
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12
                    }
                }
            }
        }
    });
    
    // Show the graphs section
    performanceGraphsSection.style.display = 'block';
}

// Create activity heatmap
function createActivityHeatmap(scores) {
    if (!scores || scores.length === 0) return;
    
    // Clear previous heatmap
    d3.select('#activity-heatmap').html('');
    
    // Prepare data for heatmap
    const heatmapData = [];
    const metrics = ['GitHub PRs', 'GitHub Commits', 'GitHub Reviews', 'Jira Tickets', 'Story Points'];
    
    scores.slice(0, 10).forEach(score => {
        heatmapData.push({
            engineer: score.engineer,
            metric: 'GitHub PRs',
            value: score.github_stats.prs_created
        });
        
        heatmapData.push({
            engineer: score.engineer,
            metric: 'GitHub Commits',
            value: score.github_stats.commits_made
        });
        
        heatmapData.push({
            engineer: score.engineer,
            metric: 'GitHub Reviews',
            value: score.github_stats.prs_reviewed
        });
        
        heatmapData.push({
            engineer: score.engineer,
            metric: 'Jira Tickets',
            value: score.jira_stats.tickets_completed
        });
        
        heatmapData.push({
            engineer: score.engineer,
            metric: 'Story Points',
            value: score.jira_stats.story_points
        });
    });
    
    // Set up heatmap dimensions
    const margin = { top: 30, right: 30, bottom: 30, left: 100 };
    const width = Math.max(400, scores.length * 50) - margin.left - margin.right;
    const height = 250 - margin.top - margin.bottom;
    
    // Create SVG
    const svg = d3.select('#activity-heatmap')
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Create scales
    const engineers = [...new Set(heatmapData.map(d => d.engineer))];
    const x = d3.scaleBand()
        .range([0, width])
        .domain(engineers)
        .padding(0.05);
    
    const y = d3.scaleBand()
        .range([height, 0])
        .domain(metrics)
        .padding(0.05);
    
    // Create color scale
    const maxValue = d3.max(heatmapData, d => d.value);
    const colorScale = d3.scaleSequential()
        .interpolator(d3.interpolateBlues)
        .domain([0, maxValue]);
    
    // Add X axis labels
    svg.append('g')
        .style('font-size', 12)
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x).tickSize(0))
        .select('.domain').remove();
    
    // Add Y axis labels
    svg.append('g')
        .style('font-size', 12)
        .call(d3.axisLeft(y).tickSize(0))
        .select('.domain').remove();
    
    // Create tooltip
    const tooltip = d3.select('#activity-heatmap')
        .append('div')
        .style('opacity', 0)
        .attr('class', 'tooltip')
        .style('background-color', 'white')
        .style('border', 'solid')
        .style('border-width', '1px')
        .style('border-radius', '5px')
        .style('padding', '5px')
        .style('position', 'absolute')
        .style('z-index', '10');
    
    // Add heatmap cells
    svg.selectAll()
        .data(heatmapData)
        .enter()
        .append('rect')
        .attr('x', d => x(d.engineer))
        .attr('y', d => y(d.metric))
        .attr('width', x.bandwidth())
        .attr('height', y.bandwidth())
        .attr('class', 'heatmap-cell')
        .style('fill', d => colorScale(d.value))
        .on('mouseover', function(event, d) {
            tooltip.style('opacity', 1);
            d3.select(this)
                .style('stroke', 'black')
                .style('stroke-width', 2);
        })
        .on('mousemove', function(event, d) {
            tooltip
                .html(`${d.engineer}<br>${d.metric}: ${d.value}`)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px');
        })
        .on('mouseleave', function() {
            tooltip.style('opacity', 0);
            d3.select(this)
                .style('stroke', 'white')
                .style('stroke-width', 1);
        });
    
    // Add legend
    const legend = svg.append('g')
        .attr('class', 'legend')
        .attr('transform', `translate(${width - 100}, -20)`);
    
    const legendValues = [0, maxValue / 4, maxValue / 2, 3 * maxValue / 4, maxValue];
    
    legend.selectAll('rect')
        .data(legendValues)
        .enter()
        .append('rect')
        .attr('x', (d, i) => i * 20)
        .attr('width', 20)
        .attr('height', 10)
        .style('fill', d => colorScale(d));
    
    legend.selectAll('text')
        .data(legendValues)
        .enter()
        .append('text')
        .attr('x', (d, i) => i * 20)
        .attr('y', 25)
        .text(d => Math.round(d))
        .style('font-size', '10px');
    
    // Show the heatmap section
    activityHeatmapSection.style.display = 'block';
}

// Mock API for testing
function mockAnalysisAPI() {
    // Override the fetch function for testing
    window.originalFetch = window.fetch;
    
    window.fetch = function(url, options) {
        if (url === '/api/productivity/analyze') {
            return new Promise((resolve) => {
                // Simulate network delay
                setTimeout(() => {
                    resolve({
                        ok: true,
                        json: () => Promise.resolve(getMockData())
                    });
                }, 2000);
            });
        }
        
        // For all other requests, use the original fetch
        return window.originalFetch(url, options);
    };
}

// Get mock data for testing
function getMockData() {
    return {
        timestamp: new Date().toISOString(),
        period: `${startDateInput.value} to ${endDateInput.value}`,
        scores: [
            {
                engineer: "Alice Smith",
                total_score: 92.5,
                github_score: 95.0,
                jira_score: 88.0,
                quality_score: 96.0,
                collaboration_score: 91.0,
                percentile_rank: 99.0,
                github_stats: {
                    prs_created: 12,
                    prs_reviewed: 18,
                    commits_made: 45,
                    lines_added: 1250,
                    lines_deleted: 580
                },
                jira_stats: {
                    tickets_completed: 8,
                    tickets_in_progress: 2,
                    story_points: 35,
                    avg_completion_time: "3.2 days"
                }
            },
            {
                engineer: "Bob Johnson",
                total_score: 87.3,
                github_score: 82.0,
                jira_score: 91.0,
                quality_score: 89.0,
                collaboration_score: 87.0,
                percentile_rank: 92.0,
                github_stats: {
                    prs_created: 8,
                    prs_reviewed: 22,
                    commits_made: 38,
                    lines_added: 980,
                    lines_deleted: 420
                },
                jira_stats: {
                    tickets_completed: 10,
                    tickets_in_progress: 1,
                    story_points: 42,
                    avg_completion_time: "2.8 days"
                }
            },
            {
                engineer: "Carol Davis",
                total_score: 85.1,
                github_score: 88.0,
                jira_score: 84.0,
                quality_score: 85.0,
                collaboration_score: 83.0,
                percentile_rank: 88.0,
                github_stats: {
                    prs_created: 10,
                    prs_reviewed: 15,
                    commits_made: 42,
                    lines_added: 1100,
                    lines_deleted: 650
                },
                jira_stats: {
                    tickets_completed: 7,
                    tickets_in_progress: 3,
                    story_points: 32,
                    avg_completion_time: "3.5 days"
                }
            },
            {
                engineer: "David Wilson",
                total_score: 82.7,
                github_score: 80.0,
                jira_score: 86.0,
                quality_score: 81.0,
                collaboration_score: 84.0,
                percentile_rank: 85.0,
                github_stats: {
                    prs_created: 7,
                    prs_reviewed: 12,
                    commits_made: 35,
                    lines_added: 920,
                    lines_deleted: 480
                },
                jira_stats: {
                    tickets_completed: 9,
                    tickets_in_progress: 2,
                    story_points: 38,
                    avg_completion_time: "3.0 days"
                }
            },
            {
                engineer: "Eve Brown",
                total_score: 79.8,
                github_score: 78.0,
                jira_score: 82.0,
                quality_score: 80.0,
                collaboration_score: 79.0,
                percentile_rank: 80.0,
                github_stats: {
                    prs_created: 6,
                    prs_reviewed: 10,
                    commits_made: 30,
                    lines_added: 850,
                    lines_deleted: 390
                },
                jira_stats: {
                    tickets_completed: 8,
                    tickets_in_progress: 1,
                    story_points: 30,
                    avg_completion_time: "3.8 days"
                }
            }
        ],
        summary: {
            executive_summary: "The team has shown strong performance during this period with an average score of 85.5. Alice Smith leads with exceptional GitHub contributions and code quality. Bob Johnson excels in Jira ticket completion. Overall collaboration is strong, with cross-team code reviews increasing by 15% compared to the previous period."
        },
        github_data: {
            total_prs: 43,
            total_commits: 190,
            total_reviews: 77
        },
        jira_data: {
            total_issues: 52,
            completed_issues: 42
        }
    };
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
    
    // Auto-run analysis with default date range (last 7 days)
    setTimeout(() => {
        runAnalysis();
    }, 1000);
    
    // Uncomment for testing with mock data
    // mockAnalysisAPI();
});