// components/DealDashboard.tsx
import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Calendar, Clock, DollarSign, ExternalLink, Filter, RefreshCw, TrendingUp, AlertTriangle } from 'lucide-react';
import { useEventSource } from '@/hooks/useEventSource';

interface Deal {
id: string;
provider: string;
category: string;
title: string;
description: string;
trialDays?: number;
creditUSD?: number;
originalPrice?: number;
discountPercentage?: number;
expiry?: string;
coupon?: string;
url: string;
source: string;
reliability: number;
popularity?: number;
score: number;
scrapedAt: string;
features?: string[];
limitations?: string[];
targetAudience?: string[];
trending?: boolean;
}

export default function DealDashboard() {
const [deals, setDeals] = useState<Deal[]>([]);
const [filteredDeals, setFilteredDeals] = useState<Deal[]>([]);
const [loading, setLoading] = useState(true);
const [selectedCategory, setSelectedCategory] = useState<string>('all');
const [sortBy, setSortBy] = useState<string>('score');
const [showTrendingOnly, setShowTrendingOnly] = useState(false);
const [urgentOnly, setUrgentOnly] = useState(false);
const lastUpdate = useRef<Date | null>(null);

// Set up SSE for real-time updates
const { data, error } = useEventSource('/api/deals/stream');

useEffect(() => {
if (data && data.type === 'deals') {
setDeals(data.data);
setLoading(false);
lastUpdate.current = new Date();
} else if (data && data.type === 'update') {
setDeals(prevDeals => {
// Update existing deals or add new ones
const updatedDeals = [...prevDeals];
const dealIndex = updatedDeals.findIndex(d => d.id === data.data.id);

if (dealIndex >= 0) {
updatedDeals[dealIndex] = data.data;
} else {
updatedDeals.push(data.data);
}

return updatedDeals;
});
lastUpdate.current = new Date();
}
}, [data]);

useEffect(() => {
filterAndSortDeals();
}, [deals, selectedCategory, sortBy, showTrendingOnly, urgentOnly]);

const filterAndSortDeals = () => {
let filtered = [...deals];

// Filter by category
if (selectedCategory !== 'all') {
filtered = filtered.filter(deal => deal.category === selectedCategory);
}

// Filter by trending
if (showTrendingOnly) {
filtered = filtered.filter(deal => deal.trending);
}

// Filter by urgent (expiring soon)
if (urgentOnly) {
filtered = filtered.filter(deal => {
if (!deal.expiry) return false;
const daysUntilExpiry = (new Date(deal.expiry).getTime() - Date.now()) / (1000 * 60 * 60 * 24);
return daysUntilExpiry < 7;
});
}

// Sort by selected criteria
filtered.sort((a, b) => {
switch (sortBy) {
case 'score':
return b.score - a.score;
case 'expiry':
return a.expiry && b.expiry ?
new Date(a.expiry).getTime() - new Date(b.expiry).getTime() : 0;
case 'value':
const aValue = (a.creditUSD || 0) + (a.trialDays || 0) * 2;
const bValue = (b.creditUSD || 0) + (b.trialDays || 0) * 2;
return bValue - aValue;
case 'popularity':
return (b.popularity || 0) - (a.popularity || 0);
default:
return 0;
}
});

setFilteredDeals(filtered);
};

const getDaysUntilExpiry = (expiry?: string) => {
if (!expiry) return null;
const days = Math.ceil((new Date(expiry).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));
return days;
};

const getExpiryColor = (days?: number) => {
if (!days) return 'secondary';
if (days < 3) return 'destructive';
if (days < 7) return 'destructive';
if (days < 14) return 'outline';
return 'secondary';
};

const categories = ['all', ...Array.from(new Set(deals.map(deal => deal.category)))];

const refreshDeals = async () => {
setLoading(true);
try {
const response = await fetch('/api/deals/refresh', { method: 'POST' });
if (response.ok) {
// The SSE will update the deals when ready
console.log('Deal refresh triggered');
}
} catch (error) {
console.error('Failed to refresh deals:', error);
setLoading(false);
}
};

return (
<Card>
<CardHeader>
<CardTitle className="flex justify-between items-center">
AI Tool Deals
<div className="flex items-center gap-2">
<Button variant="outline" size="sm" onClick={refreshDeals} disabled={loading}>
<RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
Refresh
</Button>
<span className="text-sm text-gray-500">
Last updated: {lastUpdate.current ? lastUpdate.current.toLocaleTimeString() : 'N/A'}
</span>
</div>
</CardTitle>
</CardHeader>
<CardContent>
<div className="flex flex-col gap-4">
<div className="flex items-center gap-4">
<h3 className="text-lg font-semibold">Filters:</h3>
<div className="flex items-center gap-2">
<span className="font-semibold">Category:</span>
{categories.map(category => (
<Badge
key={category}
variant={selectedCategory === category ? 'default' : 'outline'}
className="cursor-pointer"
onClick={() => setSelectedCategory(category)}
>
{category}
</Badge>
))}
</div>
<Button
variant={showTrendingOnly ? 'default' : 'outline'}
className="cursor-pointer flex items-center gap-1"
onClick={() => setShowTrendingOnly(!showTrendingOnly)}
>
<TrendingUp className="h-4 w-4" />
Trending
</Button>
<Button
variant={urgentOnly ? 'default' : 'outline'}
className="cursor-pointer flex items-center gap-1"
onClick={() => setUrgentOnly(!urgentOnly)}
>
<AlertTriangle className="h-4 w-4" />
Urgent
</Button>
</div>
<Tabs defaultValue="card" className="w-full">
<TabsList>
<TabsTrigger value="card">Card View</TabsTrigger>
<TabsTrigger value="list">List View</TabsTrigger>
<TabsTrigger value="analytics">Analytics</TabsTrigger>
</TabsList>
<TabsContent value="card">
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
{filteredDeals.map(deal => (
<DealCard key={deal.id} deal={deal} />
))}
</div>
</TabsContent>
<TabsContent value="list">
<div className="flex flex-col gap-2">
{filteredDeals.map(deal => (
<DealListItem key={deal.id} deal={deal} />
))}
</div>
</TabsContent>
<TabsContent value="analytics">
<DealAnalytics deals={deals} />
</TabsContent>
</Tabs>
</div>
</CardContent>
</Card>
);
}

function DealCard({ deal }: { deal: Deal }) {
const daysUntilExpiry = getDaysUntilExpiry(deal.expiry);

return (
<Card className="flex flex-col">
<CardHeader>
<CardTitle className="flex justify-between items-start">
<span className="text-lg">{deal.title}</span>
{deal.trending && (
<Badge variant="destructive" className="flex items-center gap-1">
<TrendingUp className="h-4 w-4" />
Trending
</Badge>
)}
</CardTitle>
<p className="text-sm text-gray-500">{deal.provider}</p>
</CardHeader>
<CardContent className="flex-grow">
<p className="text-sm">{deal.description}</p>
<div className="flex flex-wrap gap-2 mt-4">
{deal.trialDays && (
<Badge variant="secondary" className="flex items-center gap-1">
<Calendar className="h-4 w-4" />
{deal.trialDays} days
</Badge>
)}
{deal.creditUSD && (
<Badge variant="secondary" className="flex items-center gap-1">
<DollarSign className="h-4 w-4" />
${deal.creditUSD}
</Badge>
)}
{deal.discountPercentage && (
<Badge variant="secondary">{deal.discountPercentage}% off</Badge>
)}
{daysUntilExpiry !== null && (
<Badge variant={getExpiryColor(daysUntilExpiry)} className="flex items-center gap-1">
<Clock className="h-4 w-4" />
{daysUntilExpiry} days left
</Badge>
)}
</div>
</CardContent>
<div className="p-4 border-t">
{deal.coupon && (
<div className="flex justify-between items-center">
<span className="text-sm">Coupon:</span>
<Badge variant="outline">{deal.coupon}</Badge>
</div>
)}
<Button asChild className="w-full mt-2">
<a href={deal.url} target="_blank" rel="noopener noreferrer">
View Deal <ExternalLink className="ml-2 h-4 w-4" />
</a>
</Button>
</div>
</Card>
);
}

function DealListItem({ deal }: { deal: Deal }) {
const daysUntilExpiry = getDaysUntilExpiry(deal.expiry);

return (
<div className="flex items-center justify-between p-2 border rounded-md">
<div className="flex flex-col">
<div className="flex items-center gap-2">
<span className="font-semibold">{deal.title}</span>
<span className="text-sm text-gray-500">({deal.provider})</span>
{deal.trending && (
<Badge variant="destructive" className="flex items-center gap-1">
<TrendingUp className="h-4 w-4" />
Trending
</Badge>
)}
</div>
<p className="text-sm text-gray-600">{deal.description}</p>
</div>
<div className="flex items-center gap-4">
<div className="flex flex-wrap gap-2">
{deal.trialDays && (
<Badge variant="secondary" className="flex items-center gap-1">
<Calendar className="h-4 w-4" />
{deal.trialDays} days
</Badge>
)}
{deal.creditUSD && (
<Badge variant="secondary" className="flex items-center gap-1">
<DollarSign className="h-4 w-4" />
${deal.creditUSD}
</Badge>
)}
{deal.discountPercentage && (
<Badge variant="secondary">{deal.discountPercentage}% off</Badge>
)}
{daysUntilExpiry !== null && (
<Badge variant={getExpiryColor(daysUntilExpiry)} className="flex items-center gap-1">
<Clock className="h-4 w-4" />
{daysUntilExpiry} days left
</Badge>
)}
</div>
{deal.coupon && (
<div className="flex items-center gap-2">
<span className="text-sm">Coupon:</span>
<Badge variant="outline">{deal.coupon}</Badge>
</div>
)}
<Button asChild size="sm">
<a href={deal.url} target="_blank" rel="noopener noreferrer">
<ExternalLink className="h-4 w-4" />
</a>
</Button>
</div>
</div>
);
}

function DealAnalytics({ deals }: { deals: Deal[] }) {
const categoryCounts = deals.reduce((acc, deal) => {
acc[deal.category] = (acc[deal.category] || 0) + 1;
return acc;
}, {} as Record<string, number>);

const averageScore = deals.length > 0 ? deals.reduce((sum, deal) => sum + deal.score, 0) / deals.length : 0;
const averageCredit = deals.length > 0 ? deals.reduce((sum, deal) => sum + (deal.creditUSD || 0), 0) / deals.length : 0;
const averageTrial = deals.length > 0 ? deals.reduce((sum, deal) => sum + (deal.trialDays || 0), 0) / deals.length : 0;

const expiringSoon = deals.filter(deal => {
if (!deal.expiry) return false;
const daysUntilExpiry = (new Date(deal.expiry).getTime() - Date.now()) / (1000 * 60 * 60 * 24);
return daysUntilExpiry < 7;
}).length;

const trendingCount = deals.filter(deal => deal.trending).length;

return (
<div className="grid grid-cols-2 md:grid-cols-4 gap-4">
<Card>
<CardHeader>
<CardTitle>Total Deals</CardTitle>
</CardHeader>
<CardContent>
<p className="text-2xl font-bold">{deals.length}</p>
</CardContent>
</Card>
<Card>
<CardHeader>
<CardTitle>Average Score</CardTitle>
</CardHeader>
<CardContent>
<p className="text-2xl font-bold">{averageScore.toFixed(1)}</p>
</CardContent>
</Card>
<Card>
<CardHeader>
<CardTitle>Expiring Soon</CardTitle>
</CardHeader>
<CardContent>
<p className="text-2xl font-bold">{expiringSoon}</p>
</CardContent>
</Card>
<Card>
<CardHeader>
<CardTitle>Trending Deals</CardTitle>
</CardHeader>
<CardContent>
<p className="text-2xl font-bold">{trendingCount}</p>
</CardContent>
</Card>
<Card className="col-span-2">
<CardHeader>
<CardTitle>Average Deal Value</CardTitle>
</CardHeader>
<CardContent className="flex gap-4">
<div>
<p className="text-sm text-gray-500">Credit:</p>
<p className="text-lg font-semibold">${averageCredit.toFixed(2)}</p>
</div>
<div>
<p className="text-sm text-gray-500">Trial Days:</p>
<p className="text-lg font-semibold">{averageTrial.toFixed(1)}</p>
</div>
</CardContent>
</Card>
<Card className="col-span-2">
<CardHeader>
<CardTitle>Deals by Category</CardTitle>
</CardHeader>
<CardContent className="flex flex-wrap gap-2">
{Object.entries(categoryCounts).map(([category, count]) => (
<Badge key={category} variant="outline">
{category}:
<span className="font-semibold ml-1">{count}</span>
</Badge>
))}
</CardContent>
</Card>
</div>
);
}
