import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Activity, ArrowDownRight, ArrowUpRight, BarChart3, CalendarDays, Check,
  ChevronRight, CircleHelp, CreditCard, DollarSign, Landmark, LayoutDashboard,
  LoaderCircle, LogOut, Menu, Moon, Plus, RefreshCw, ShieldCheck, Sparkles,
  Sun, Target, Trash2, TrendingDown, TrendingUp, Users, UserCog, Wallet,
  X, Pencil, ReceiptText, CircleDollarSign, Search, KeyRound, UserRound,
  ChevronDown, ChevronLeft,
} from 'lucide-react';
import { api, jsonRequest } from './services/api.js';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'income', label: 'Income', icon: TrendingUp },
  { id: 'expenses', label: 'Expenses', icon: TrendingDown },
  { id: 'limits', label: 'Expense Limits', icon: Target },
  { id: 'profile', label: 'Profile', icon: UserRound },
];
const ADMIN_NAV = [
  { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
  { id: 'users', label: 'User Management', icon: Users },
  { id: 'administrators', label: 'Administrators', icon: UserCog },
  { id: 'profile', label: 'Profile', icon: UserRound },
];

const currentMonth = () => {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Jakarta', year: 'numeric', month: '2-digit',
  }).formatToParts(new Date());
  const values = Object.fromEntries(parts.map(({ type, value }) => [type, value]));
  return `${values.year}-${values.month}`;
};
const formatMoney = (value) => new Intl.NumberFormat('id-ID', {
  style: 'currency', currency: 'IDR', maximumFractionDigits: 0,
}).format(Number(value || 0));
const formatMonth = (value) => {
  if (!value) return '—';
  const [year, month] = value.split('-').map(Number);
  return new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric' }).format(new Date(year, month - 1, 1));
};

const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

function MokiMark({ size = 19 }) {
  return <svg className="moki-mark" width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <path d="M5.1 9.4 4 3.8l5.2 3a8.2 8.2 0 0 1 5.6 0l5.2-3-1.1 5.6c.8 1 1.2 2.1 1.2 3.5 0 4.1-3.6 7.2-8.1 7.2s-8.1-3.1-8.1-7.2c0-1.4.4-2.5 1.2-3.5Z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
    <path d="M9 12.2h.01M15 12.2h.01M10 15.1c1.2.9 2.8.9 4 0M12 13.2l-.8 1h1.6l-.8-1Z" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    <path d="m5.3 14.2-2.1.3m2.5 1.6-1.9 1m14.9-2.9 2.1.3m-2.5 1.6 1.9 1" stroke="currentColor" strokeWidth="1.35" strokeLinecap="round" />
  </svg>;
}

function ThemeToggle({ theme, onToggle }) {
  return <button type="button" className="icon-button theme-toggle" onClick={onToggle}
    title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
    aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}>
    {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
  </button>;
}

function Toast({ toast, onClose }) {
  if (!toast) return null;
  return <div className={`toast toast-${toast.type || 'success'}`} role="status">
    {toast.type === 'error' ? <CircleHelp size={17} /> : <Check size={17} />}
    <span>{toast.message}</span>
    <button className="icon-button toast-close" onClick={onClose} aria-label="Dismiss notification"><X size={15} /></button>
  </div>;
}
function LoadingBlock({ label = 'Loading your workspace' }) {
  return <div className="loading-block"><LoaderCircle className="spin" size={22} /><span>{label}</span></div>;
}
function Button({ children, variant = 'primary', size = '', ...props }) {
  return <button className={`button button-${variant} ${size ? `button-${size}` : ''}`} {...props}>{children}</button>;
}
function Field({ label, children, hint }) {
  return <label className="field"><span className="field-label">{label}</span>{children}{hint && <small className="field-hint">{hint}</small>}</label>;
}
function MonthSelector({ month, onChange, label = 'Select month' }) {
  const [open, setOpen] = useState(false);
  const [year, setYear] = useState(() => Number((month || currentMonth()).slice(0, 4)));
  const rootRef = useRef(null);
  const selectedMonth = Number((month || currentMonth()).slice(5, 7)) - 1;

  useEffect(() => { setYear(Number((month || currentMonth()).slice(0, 4))); }, [month]);
  useEffect(() => {
    function handlePointer(event) {
      if (rootRef.current && !rootRef.current.contains(event.target)) setOpen(false);
    }
    function handleKey(event) { if (event.key === 'Escape') setOpen(false); }
    document.addEventListener('pointerdown', handlePointer);
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('pointerdown', handlePointer);
      document.removeEventListener('keydown', handleKey);
    };
  }, []);

  function chooseMonth(index) {
    onChange(`${year}-${String(index + 1).padStart(2, '0')}`);
    setOpen(false);
  }

  return <div className="month-select" ref={rootRef}>
    <button type="button" className={`month-select-trigger ${open ? 'month-select-open' : ''}`} onClick={() => setOpen((value) => !value)}
      aria-label={label} aria-haspopup="dialog" aria-expanded={open}>
      <CalendarDays size={17} />
      <span className="month-select-value">{formatMonth(month)}</span>
      <ChevronDown size={15} className="month-select-chevron" />
    </button>
    {open && <div className="month-select-popover" role="dialog" aria-label={label}>
      <div className="month-select-year">
        <button type="button" className="icon-button" onClick={() => setYear((value) => value - 1)} aria-label="Previous year"><ChevronLeft size={17} /></button>
        <strong>{year}</strong>
        <button type="button" className="icon-button" onClick={() => setYear((value) => value + 1)} aria-label="Next year"><ChevronRight size={17} /></button>
      </div>
      <div className="month-select-grid">
        {MONTH_NAMES.map((name, index) => {
          const isSelected = year === Number((month || currentMonth()).slice(0, 4)) && index === selectedMonth;
          return <button type="button" key={name} className={isSelected ? 'month-option month-option-selected' : 'month-option'}
            onClick={() => chooseMonth(index)}>{name.slice(0, 3)}</button>;
        })}
      </div>
      <div className="month-select-footer">
        <button type="button" onClick={() => { const value = currentMonth(); onChange(value); setOpen(false); }}>Current month</button>
        <button type="button" onClick={() => setOpen(false)}>Close</button>
      </div>
    </div>}
  </div>;
}

function AuthScreen({ onAuthenticated, theme, onToggleTheme }) {
  const [mode, setMode] = useState('login');
  const [name, setName] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [csrfReady, setCsrfReady] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => { api('/auth/csrf').then(() => setCsrfReady(true)).catch((err) => setError(err.message)); }, []);

  async function submit(event) {
    event.preventDefault(); setBusy(true); setError('');
    try {
      const result = await api(`/auth/${mode === 'login' ? 'login' : 'register'}`,
        jsonRequest('POST', mode === 'login' ? { username, password } : { name, username, password }));
      onAuthenticated(result.user);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  return <div className="user-auth-shell">
    <div className="user-auth-topbar">
      <div className="brand"><span className="brand-mark"><MokiMark /></span><span>moki</span></div>
      <ThemeToggle theme={theme} onToggle={onToggleTheme} />
    </div>
    <main className="user-auth-card">
      <span className="eyebrow">{mode === 'login' ? 'WELCOME BACK' : 'GET STARTED'}</span>
      <h1>{mode === 'login' ? 'Sign in to Moki' : 'Create your account'}</h1>
      <p className="user-auth-subtitle">{mode === 'login' ? 'A clearer view of your money starts here.' : 'Build a clearer picture of your finances.'}</p>
      <form onSubmit={submit} className="auth-form">
        {mode === 'register' && <Field label="Full name"><input autoComplete="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Alex Morgan" required maxLength={80} /></Field>}
        <Field label="Username" hint="3–50 characters · lowercase letters, numbers, and underscores"><input autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="your_username" required minLength={3} maxLength={50} pattern="[a-zA-Z0-9_]{3,50}" /></Field>
        <Field label="Password" hint="Use at least 6 characters."><input type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter your password" minLength={6} maxLength={128} required /></Field>
        {error && <div className="inline-error">{error}</div>}
        <Button type="submit" disabled={busy || !csrfReady}>{busy ? <LoaderCircle className="spin" size={17} /> : null}{mode === 'login' ? 'Sign in' : 'Create account'}<ArrowUpRight size={17} /></Button>
      </form>
      <p className="auth-switch">{mode === 'login' ? 'New to Moki?' : 'Already have an account?'} <button onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }}>{mode === 'login' ? 'Create an account' : 'Sign in instead'}</button></p>
      <div className="auth-security"><ShieldCheck size={15} /> Your data is private to your account.</div>
    </main>
    <footer className="user-auth-footer">Thoughtful money management, made simple.</footer>
  </div>;
}

function MetricCard({ label, value, icon: Icon, tone = 'neutral', note }) {
  return <div className="metric-card"><div className="metric-top"><span>{label}</span><span className={`metric-icon metric-${tone}`}><Icon size={17} /></span></div><div className="metric-value">{formatMoney(value)}</div>{note && <div className="metric-note">{note}</div>}</div>;
}
function ChartPanel({ title, subtitle, children, action }) {
  return <section className="panel chart-panel"><div className="panel-heading"><div><h3>{title}</h3>{subtitle && <p>{subtitle}</p>}</div>{action}</div>{children}</section>;
}
function Donut({ spent, limit, label }) {
  const ratio = limit > 0 ? Math.min(spent / limit, 1) : 0;
  const percent = limit > 0 ? Math.round((spent / limit) * 100) : 0;
  const over = Math.max(0, spent - limit);
  const remaining = Math.max(0, limit - spent);
  return <div className="donut-wrap"><div className="donut" style={{ '--ratio': `${ratio * 100}%` }}><div className="donut-center"><strong>{limit > 0 ? `${percent}%` : '0%'}</strong><span>used</span></div></div><div className="donut-legend">
    <div><i className="legend-dot dot-spent" /><span>Spent</span><strong>{formatMoney(spent)}</strong></div>
    <div><i className="legend-dot dot-remaining" /><span>{over > 0 ? 'Limit exceeded' : 'Remaining'}</span><strong>{formatMoney(over > 0 ? over : remaining)}</strong></div>
    <div className="legend-total"><span>{label}</span><strong>{formatMoney(limit)}</strong></div>
  </div></div>;
}

const ALLOCATION_COLORS = ['#9b8cff', '#54c6a0', '#f0a56d', '#77b9ed', '#e879a9', '#e6c45f', '#8da4c5', '#9dca76', '#d18bf1'];
function IncomeAllocation({ income, expenses, remainingIncome }) {
  const entries = expenses.filter((item) => Number(item.amount) > 0);
  // Keep Remaining Income in the legend even when it is zero. Negative
  // balances cannot be represented as a donut slice, so the deficit is
  // shown separately below.
  entries.push({ description: 'Remaining Income', amount: Math.max(0, remainingIncome), isRemaining: true });
  const spent = expenses.reduce((sum, item) => sum + Number(item.amount), 0);
  const displayTotal = income > 0 ? Math.max(income, spent) : spent;
  let cursor = 0;
  const stops = entries.map((entry, index) => {
    const percent = displayTotal > 0 ? (Number(entry.amount) / displayTotal) * 100 : 0;
    const start = cursor; cursor += percent;
    return { ...entry, color: entry.isRemaining ? '#53657e' : ALLOCATION_COLORS[index % ALLOCATION_COLORS.length], start, end: cursor,
      incomePercent: income > 0 ? (Number(entry.amount) / income) * 100 : null };
  });
  const gradient = stops.length ? `conic-gradient(${stops.map((item) => `${item.color} ${item.start}% ${item.end}%`).join(', ')})` : 'conic-gradient(var(--surface-3) 0 100%)';
  const deficit = Math.max(0, spent - income);
  const hasFinancialData = income > 0 || spent > 0;
  return <div className="allocation-layout">
    <div className="allocation-donut" style={{ background: hasFinancialData ? gradient : 'conic-gradient(var(--surface-3) 0 100%)' }}><div className="allocation-center"><strong>{formatMoney(income)}</strong><span>Total income</span></div></div>
    <div className="allocation-legend">{!hasFinancialData ? <div className="allocation-empty">No income or expenses recorded for this month.</div> : stops.map((item) => <div className="allocation-item" key={item.description}>
      <i style={{ background: item.color }} /><span>{item.description}</span><strong>{formatMoney(item.amount)}</strong><small>{item.incomePercent === null ? '—' : `${item.incomePercent.toFixed(1)}% of income`}</small>
    </div>)}
      {deficit > 0 && <div className="allocation-deficit"><TrendingDown size={15} /><span>Expenses exceed income by <strong>{formatMoney(deficit)}</strong>. The ring shows expense composition; percentages remain measured against total income.</span></div>}
      {income > 0 && spent <= income && <p className="allocation-note">Each expense component and remaining income adds up to 100% of total income.</p>}
      {income === 0 && spent > 0 && <p className="allocation-note">Total income is zero, so expense percentages cannot be calculated.</p>}
    </div>
  </div>;
}

function DashboardPage({ month, onMonthChange, onNavigate, refreshKey }) {
  const [data, setData] = useState(null); const [loading, setLoading] = useState(true); const [error, setError] = useState('');
  const load = useCallback(async () => { setLoading(true); setError(''); try { setData(await api(`/dashboard?month=${encodeURIComponent(month)}`)); } catch (err) { setError(err.message); } finally { setLoading(false); } }, [month, refreshKey]);
  useEffect(() => { load(); }, [load]);
  if (loading) return <LoadingBlock />;
  if (error) return <div className="panel error-panel">{error} <Button variant="secondary" size="small" onClick={load}><RefreshCw size={15} /> Retry</Button></div>;
  const m = data.metrics;
  const cards = [
    { label: 'Expense Limit', value: m.expense_limit, icon: Target, tone: 'purple' },
    { label: 'Total Income', value: m.total_income, icon: Wallet, tone: 'green' },
    { label: 'Fixed Income', value: m.fixed_income, icon: Landmark, tone: 'green' },
    { label: 'Additional Income', value: m.additional_income, icon: TrendingUp, tone: 'green' },
    { label: 'Total Expenses', value: m.total_expenses, icon: CreditCard, tone: 'orange' },
    { label: 'Fixed Expenses', value: m.fixed_expenses, icon: ReceiptText, tone: 'orange' },
    { label: 'Additional Expenses', value: m.additional_expenses, icon: Activity, tone: 'orange' },
    { label: 'All-Time Income', value: data.all_time_income, icon: Wallet, tone: 'blue', note: 'Through selected month' },
    { label: 'All-Time Expenses', value: data.all_time_expenses, icon: CreditCard, tone: 'orange', note: 'Through selected month' },
    { label: 'Surplus / Deficit', value: m.surplus_deficit, icon: m.surplus_deficit >= 0 ? ArrowUpRight : ArrowDownRight, tone: m.surplus_deficit >= 0 ? 'green' : 'red' },
    { label: 'Fixed Income Balance', value: m.fixed_income_balance, icon: CircleDollarSign, tone: m.fixed_income_balance >= 0 ? 'blue' : 'red' },
    { label: 'Remaining Fixed Income', value: m.remaining_fixed_income, icon: DollarSign, tone: m.remaining_fixed_income >= 0 ? 'blue' : 'red' },
  ];
  const maxExpense = Math.max(1, ...data.expense_breakdown.map((item) => item.amount));
  return <div className="page-content">
    <div className="page-toolbar"><div><span className="toolbar-eyebrow">FINANCIAL OVERVIEW</span><strong>{formatMonth(month)}</strong><small>Choose a month to review its financial activity.</small></div><MonthSelector month={month} onChange={onMonthChange} label="Dashboard month" /></div>
    <div className="metrics-grid">{cards.map((card) => <MetricCard key={card.label} {...card} />)}</div>
    <div className="dashboard-charts">
      <ChartPanel title="Expense Limit Overview" subtitle="How your spending compares with the monthly limit."><Donut spent={m.total_expenses} limit={m.expense_limit} label="Total limit" /></ChartPanel>
      <ChartPanel title="Fixed Expense Limit Overview" subtitle="Your fixed spending against its allocated limit."><Donut spent={m.fixed_expenses} limit={m.fixed_expense_limit} label="Fixed limit" />{m.remaining_fixed_income < 0 && <div className="deficit-note"><TrendingDown size={15} /><span>Fixed income shortfall after all expenses: <strong>{formatMoney(Math.abs(m.remaining_fixed_income))}</strong></span></div>}</ChartPanel>
    </div>
    <ChartPanel title="Income Allocation" subtitle="Each expense component as a share of total income, including the remaining income."><IncomeAllocation income={m.total_income} expenses={data.expense_breakdown} remainingIncome={m.surplus_deficit} /></ChartPanel>
    <ChartPanel title="Expense Breakdown" subtitle="Spending grouped by transaction description." action={<Button variant="ghost" size="small" onClick={() => onNavigate('expenses')}>View expenses <ArrowUpRight size={15} /></Button>}>
      {data.expense_breakdown.length === 0 ? <div className="empty-chart"><span className="empty-icon"><BarChart3 size={21} /></span><strong>No expenses yet</strong><span>Add expenses to see your spending breakdown.</span><Button size="small" onClick={() => onNavigate('expenses')}><Plus size={15} /> Add expenses</Button></div> : <div className="breakdown-list">{data.expense_breakdown.map((item, index) => <div className="breakdown-row" key={item.description}><div className="breakdown-label"><span className="breakdown-rank">{String(index + 1).padStart(2, '0')}</span><span>{item.description}</span><strong>{formatMoney(item.amount)}</strong></div><div className="bar-track"><div className="bar-fill" style={{ width: `${(item.amount / maxExpense) * 100}%` }} /></div></div>)}</div>}
    </ChartPanel>
  </div>;
}

function TransactionPage({ kind, month, onMonthChange, onChanged, refreshKey, notify }) {
  const isIncome = kind === 'income'; const title = isIncome ? 'Income' : 'Expenses';
  const [items, setItems] = useState([]); const [rows, setRows] = useState([{ description: '', type: 'fixed', amount: '' }]);
  const [loading, setLoading] = useState(true); const [saving, setSaving] = useState(false); const [editing, setEditing] = useState(null);
  const load = useCallback(async () => { setLoading(true); try { const result = await api(`/${isIncome ? 'incomes' : 'expenses'}?month=${encodeURIComponent(month)}`); setItems(result.items); } catch (err) { notify(err.message, 'error'); } finally { setLoading(false); } }, [isIncome, month, refreshKey]);
  useEffect(() => { load(); }, [load]);
  const total = items.reduce((sum, item) => sum + Number(item.amount), 0);
  function changeRow(index, field, value) { setRows((current) => current.map((row, i) => i === index ? { ...row, [field]: value } : row)); }
  function addRow() { setRows((current) => [...current, { description: '', type: 'fixed', amount: '' }]); }
  function removeRow(index) { setRows((current) => current.length === 1 ? [{ description: '', type: 'fixed', amount: '' }] : current.filter((_, i) => i !== index)); }
  async function submitBulk(event) {
    event.preventDefault();
    const validRows = rows.filter((row) => row.description.trim() && Number(row.amount) > 0);
    if (!validRows.length) { notify('Add at least one row with a description and amount greater than zero.', 'error'); return; }
    if (validRows.length !== rows.length) { notify('Complete or remove every blank row before saving.', 'error'); return; }
    setSaving(true);
    try {
      const result = await api(`/${isIncome ? 'incomes' : 'expenses'}/bulk`, jsonRequest('POST', { month, items: validRows.map((row) => ({ ...row, amount: Number(row.amount) })) }));
      notify(`${result.created} ${isIncome ? 'income entries' : 'expense entries'} added for ${formatMonth(month)}.`);
      setRows([{ description: '', type: 'fixed', amount: '' }]); await load(); onChanged();
    } catch (err) { notify(err.message, 'error'); } finally { setSaving(false); }
  }
  async function saveEdit() {
    if (!editing?.description?.trim() || Number(editing.amount) <= 0) { notify('Description and a positive amount are required.', 'error'); return; }
    try { await api(`/${isIncome ? 'incomes' : 'expenses'}/${editing.id}`, jsonRequest('PATCH', { description: editing.description.trim(), type: editing.type, amount: Number(editing.amount) })); setEditing(null); notify('Transaction updated.'); await load(); onChanged(); }
    catch (err) { notify(err.message, 'error'); }
  }
  async function deleteItem(id) {
    if (!window.confirm(`Delete this ${isIncome ? 'income' : 'expense'} entry?`)) return;
    try { await api(`/${isIncome ? 'incomes' : 'expenses'}/${id}`, { method: 'DELETE' }); notify('Transaction deleted.'); await load(); onChanged(); } catch (err) { notify(err.message, 'error'); }
  }
  return <div className="page-content">
    <div className="page-toolbar"><div><span className="toolbar-eyebrow">{isIncome ? 'MONEY COMING IN' : 'MONEY GOING OUT'}</span><strong>{formatMonth(month)}</strong><small>Select which month you are adding or reviewing.</small></div><MonthSelector month={month} onChange={onMonthChange} label={`${title} month`} /></div>
    <div className="page-intro-row"><div className="summary-tile"><span className={`summary-tile-icon ${isIncome ? 'summary-green' : 'summary-orange'}`}>{isIncome ? <TrendingUp size={19} /> : <TrendingDown size={19} />}</span><div><span className="summary-tile-label">Total {title.toLowerCase()} in {formatMonth(month)}</span><strong>{formatMoney(total)}</strong><small>{items.length} {items.length === 1 ? 'entry' : 'entries'}</small></div></div></div>
    <section className="panel"><div className="panel-heading"><div><h3>Bulk add {title.toLowerCase()}</h3><p>Add multiple entries in one go. Every row will use {formatMonth(month)}.</p></div><span className="bulk-badge"><Sparkles size={13} /> BULK ENTRY</span></div>
      <form onSubmit={submitBulk}><div className="bulk-table-head"><span>Description</span><span>Type</span><span>Amount (IDR)</span><span /></div><div className="bulk-rows">{rows.map((row, index) => <div className="bulk-row" key={index}>
        <input value={row.description} onChange={(e) => changeRow(index, 'description', e.target.value)} placeholder={isIncome ? 'e.g. Monthly salary' : 'e.g. Groceries'} aria-label="Description" maxLength={160} />
        <select value={row.type} onChange={(e) => changeRow(index, 'type', e.target.value)} aria-label="Transaction type"><option value="fixed">Fixed</option><option value="additional">Additional</option></select>
        <div className="amount-input"><span>Rp</span><input type="number" min="1" step="1" value={row.amount} onChange={(e) => changeRow(index, 'amount', e.target.value)} placeholder="0" aria-label="Amount" /></div>
        <button type="button" className="icon-button row-remove" onClick={() => removeRow(index)} aria-label="Remove row"><X size={17} /></button>
      </div>)}</div><div className="bulk-footer"><button type="button" className="text-button" onClick={addRow}><Plus size={16} /> Add another row</button><div className="bulk-actions"><span>{rows.length} {rows.length === 1 ? 'row' : 'rows'}</span><Button type="submit" disabled={saving}>{saving ? <LoaderCircle size={16} className="spin" /> : <Check size={16} />} Save all entries</Button></div></div></form>
    </section>
    <section className="panel table-panel"><div className="panel-heading"><div><h3>{title} history</h3><p>Entries recorded for {formatMonth(month)}.</p></div><Button variant="secondary" size="small" onClick={load}><RefreshCw size={14} /> Refresh</Button></div>
      {loading ? <LoadingBlock label={`Loading ${title.toLowerCase()}`} /> : items.length === 0 ? <div className="empty-table"><span className="empty-icon">{isIncome ? <Wallet size={21} /> : <CreditCard size={21} />}</span><strong>No {title.toLowerCase()} recorded</strong><span>Your entries for this month will appear here.</span></div> : <div className="table-scroll"><table><thead><tr><th>Description</th><th>Type</th><th className="align-right">Amount</th><th className="align-right">Actions</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}>
        {editing?.id === item.id ? <><td><input className="table-input" value={editing.description} onChange={(e) => setEditing({ ...editing, description: e.target.value })} /></td><td><select className="table-input" value={editing.type} onChange={(e) => setEditing({ ...editing, type: e.target.value })}><option value="fixed">Fixed</option><option value="additional">Additional</option></select></td><td><input className="table-input align-right" type="number" min="1" value={editing.amount} onChange={(e) => setEditing({ ...editing, amount: e.target.value })} /></td><td><div className="table-actions"><button className="icon-button action-save" onClick={saveEdit} title="Save"><Check size={16} /></button><button className="icon-button" onClick={() => setEditing(null)} title="Cancel"><X size={16} /></button></div></td></> : <><td><div className="transaction-description"><span className={`transaction-dot ${isIncome ? 'income-dot' : 'expense-dot'}`} />{item.description}</div></td><td><span className={`type-pill type-${item.type}`}>{item.type}</span></td><td className="align-right amount-cell">{formatMoney(item.amount)}</td><td><div className="table-actions"><button className="icon-button" onClick={() => setEditing({ ...item, amount: String(item.amount) })} title="Edit"><Pencil size={15} /></button><button className="icon-button action-delete" onClick={() => deleteItem(item.id)} title="Delete"><Trash2 size={15} /></button></div></td></>}
      </tr>)}</tbody></table></div>}
    </section>
  </div>;
}

function ExpenseLimitsPage({ month, onMonthChange, refreshKey, onChanged, notify }) {
  const [plan, setPlan] = useState(null); const [rows, setRows] = useState([]); const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true); const [saving, setSaving] = useState(false);
  const load = useCallback(async () => {
    setLoading(true);
    try { const [result, past] = await Promise.all([api(`/expense-limits?month=${encodeURIComponent(month)}`), api('/expense-limits/history')]); setPlan(result); setRows(result.components.map((component) => ({ ...component, amount: String(component.amount) }))); setHistory(past.items); }
    catch (err) { notify(err.message, 'error'); } finally { setLoading(false); }
  }, [month, refreshKey]);
  useEffect(() => { load(); }, [load]);
  const total = rows.reduce((sum, row) => sum + Math.max(0, Number(row.amount) || 0), 0);
  const fixedTotal = rows.filter((row) => row.type === 'fixed').reduce((sum, row) => sum + Math.max(0, Number(row.amount) || 0), 0);
  function updateRow(index, field, value) { setRows((current) => current.map((row, i) => i === index ? { ...row, [field]: value } : row)); }
  function addRow() { setRows((current) => [...current, { description: '', type: 'fixed', amount: '' }]); }
  function removeRow(index) { setRows((current) => current.filter((_, i) => i !== index)); }
  async function save() {
    const clean = rows.filter((row) => row.description.trim()).map((row) => ({ description: row.description.trim(), type: row.type, amount: Number(row.amount || 0) }));
    if (clean.length !== rows.length) { notify('Complete or remove rows without a description.', 'error'); return; }
    if (clean.some((row) => row.amount < 0 || !Number.isFinite(row.amount))) { notify('Enter valid amounts for every component.', 'error'); return; }
    setSaving(true);
    try { const result = await api(`/expense-limits/${month}`, jsonRequest('PUT', { components: clean })); setPlan(result); setRows(result.components.map((component) => ({ ...component, amount: String(component.amount) }))); notify(`Expense limit for ${formatMonth(month)} saved.`); await load(); onChanged(); }
    catch (err) { notify(err.message, 'error'); } finally { setSaving(false); }
  }
  async function revertToInherited() {
    if (!window.confirm(`Remove the explicit Expense Limit for ${formatMonth(month)}? This month will inherit the previous plan.`)) return;
    try { await api(`/expense-limits/${month}`, { method: 'DELETE' }); notify('Explicit plan removed. The previous plan now applies.'); await load(); onChanged(); } catch (err) { notify(err.message, 'error'); }
  }
  if (loading) return <LoadingBlock label="Loading expense limit" />;
  return <div className="page-content">
    <div className="page-toolbar"><div><span className="toolbar-eyebrow">MONTHLY SPENDING PLAN</span><strong>{formatMonth(month)}</strong><small>Choose the month for this Expense Limit revision.</small></div><MonthSelector month={month} onChange={onMonthChange} label="Expense Limit month" /></div>
    <div className="limit-summary-grid"><div className="limit-summary-main"><span className="summary-tile-icon summary-purple"><Target size={20} /></span><div><span className="summary-tile-label">Effective expense limit · {formatMonth(month)}</span><strong>{formatMoney(plan?.total_limit)}</strong><small>{plan?.is_inherited ? `Inherited from ${formatMonth(plan.source_month)}` : plan?.has_explicit_plan ? 'Explicitly set for this month' : 'No previous plan · starts at Rp0'}</small></div></div><div className="limit-mini"><span>Fixed components</span><strong>{formatMoney(plan?.fixed_limit)}</strong></div><div className="limit-mini"><span>Additional components</span><strong>{formatMoney(plan?.additional_limit)}</strong></div></div>
    <section className="panel"><div className="panel-heading"><div><h3>{plan?.has_explicit_plan ? 'Edit monthly expense limit' : 'Set expense limit'}</h3><p>{plan?.is_inherited ? `This month currently inherits ${formatMonth(plan.source_month)}. Saving here creates a new plan for ${formatMonth(month)}.` : 'Build your monthly limit from individual components.'}</p></div><span className="bulk-badge"><Target size={13} /> MONTHLY PLAN</span></div>
      <div className="limit-table-head limit-head"><span>Component description</span><span>Type</span><span>Amount (IDR)</span><span /></div><div className="limit-rows">{rows.map((row, index) => <div className="limit-row" key={index}><input value={row.description} onChange={(e) => updateRow(index, 'description', e.target.value)} placeholder="e.g. Housing" maxLength={160} /><select value={row.type} onChange={(e) => updateRow(index, 'type', e.target.value)}><option value="fixed">Fixed</option><option value="additional">Additional</option></select><div className="amount-input"><span>Rp</span><input type="number" min="0" step="1" value={row.amount} onChange={(e) => updateRow(index, 'amount', e.target.value)} placeholder="0" /></div><button className="icon-button row-remove" onClick={() => removeRow(index)} title="Remove component"><X size={17} /></button></div>)}</div>
      <div className="limit-form-footer"><button className="text-button" onClick={addRow}><Plus size={16} /> Add component</button><div className="limit-totals"><span>Fixed <strong>{formatMoney(fixedTotal)}</strong></span><span>Total <strong>{formatMoney(total)}</strong></span></div></div>
      <div className="save-plan-row"><span className="subtle-note">Saving a plan also updates months after this one until the next explicit plan.</span><div className="bulk-actions">{plan?.has_explicit_plan && <Button variant="secondary" onClick={revertToInherited}>Remove monthly plan</Button>}<Button onClick={save} disabled={saving}>{saving ? <LoaderCircle size={16} className="spin" /> : <Check size={16} />} Save expense limit</Button></div></div>
    </section>
    <section className="panel table-panel"><div className="panel-heading"><div><h3>Expense Limit history</h3><p>Explicit monthly revisions and their effective values.</p></div><span className="count-pill">{history.length} revisions</span></div>{history.length === 0 ? <div className="empty-table"><span className="empty-icon"><Target size={21} /></span><strong>No Expense Limit revisions</strong><span>Set the first plan for any month. Until then, the effective limit is Rp0.</span></div> : <div className="table-scroll"><table><thead><tr><th>Month</th><th>Source</th><th>Components</th><th className="align-right">Effective limit</th></tr></thead><tbody>{history.map((item) => <tr key={item.month}><td><strong>{formatMonth(item.month)}</strong></td><td>{item.has_explicit_plan ? 'Explicit plan' : `Inherited from ${formatMonth(item.source_month)}`}</td><td>{item.components.length}</td><td className="align-right amount-cell">{formatMoney(item.total_limit)}</td></tr>)}</tbody></table></div>}</section>
  </div>;
}

function ProfilePage({ user, onUserUpdate, notify }) {
  const [name, setName] = useState(user.name || '');
  const [username, setUsername] = useState(user.username || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setName(user.name || ''); setUsername(user.username || '');
    setCurrentPassword(''); setNewPassword(''); setConfirmPassword('');
  }, [user.id, user.name, user.username]);

  async function save(event) {
    event.preventDefault();
    if (!name.trim() || !username.trim()) { notify('Full name and username are required.', 'error'); return; }
    if (newPassword && newPassword.length < 6) { notify('New password must contain at least 6 characters.', 'error'); return; }
    if (newPassword && newPassword !== confirmPassword) { notify('New password confirmation does not match.', 'error'); return; }
    if (newPassword && !currentPassword) { notify('Enter your current password to change it.', 'error'); return; }
    setSaving(true);
    try {
      const result = await api('/auth/profile', jsonRequest('PATCH', {
        name: name.trim(), username: username.trim(),
        ...(newPassword ? { current_password: currentPassword, new_password: newPassword } : {}),
      }));
      onUserUpdate({ ...user, ...result.user });
      setCurrentPassword(''); setNewPassword(''); setConfirmPassword('');
      notify(newPassword ? 'Profile and password updated.' : 'Profile updated.');
    } catch (err) { notify(err.message, 'error'); }
    finally { setSaving(false); }
  }

  return <div className="page-content profile-page">
    <section className="panel profile-panel">
      <div className="panel-heading"><div><h3>Personal information</h3><p>Update the name and username associated with your Moki account.</p></div><span className="bulk-badge"><UserRound size={13} /> YOUR PROFILE</span></div>
      <form className="profile-form" onSubmit={save}>
        <Field label="Full name"><input value={name} onChange={(event) => setName(event.target.value)} autoComplete="name" maxLength={80} required /></Field>
        <Field label="Username" hint="3–50 characters · lowercase letters, numbers, and underscores"><input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" minLength={3} maxLength={50} pattern="[a-zA-Z0-9_]{3,50}" required /></Field>
        <div className="profile-section-divider"><span>Password</span><small>Leave the new password fields blank to keep your current password.</small></div>
        <Field label="Current password"><input type="password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} autoComplete="current-password" maxLength={128} placeholder="Required only when changing password" /></Field>
        <Field label="New password"><input type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} autoComplete="new-password" minLength={6} maxLength={128} placeholder="At least 6 characters" /></Field>
        <Field label="Confirm new password"><input type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} autoComplete="new-password" minLength={6} maxLength={128} placeholder="Re-enter new password" /></Field>
        <div className="profile-form-actions"><Button type="submit" disabled={saving}>{saving ? <LoaderCircle size={16} className="spin" /> : <Check size={16} />} Save changes</Button></div>
      </form>
    </section>
  </div>;
}

function AppShell({ user, onLogout, onUserUpdate, theme, onToggleTheme }) {
  const [activePage, setActivePage] = useState('dashboard'); const [month, setMonth] = useState(currentMonth());
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0); const [toast, setToast] = useState(null);
  const notify = (message, type = 'success') => { setToast({ message, type }); window.clearTimeout(notify.timeout); notify.timeout = window.setTimeout(() => setToast(null), 4200); };
  const activeMeta = NAV_ITEMS.find((item) => item.id === activePage) || NAV_ITEMS[0];
  function navigate(page) { setActivePage(page); setMobileNavOpen(false); }
  const refresh = () => setRefreshKey((value) => value + 1);
  return <div className="app-shell">
    <aside className={`sidebar ${mobileNavOpen ? 'sidebar-open' : ''}`}>
      <div className="sidebar-brand"><div className="brand"><span className="brand-mark"><MokiMark /></span><span>moki</span></div><span className="brand-caption">PERSONAL FINANCE</span></div>
      <div className="sidebar-section-label">WORKSPACE</div>
      <nav className="side-nav">{NAV_ITEMS.map(({ id, label, icon: Icon }) => <button key={id} className={`nav-item ${activePage === id ? 'nav-active' : ''}`} onClick={() => navigate(id)}><Icon size={18} /><span>{label}</span>{activePage === id && <i />}</button>)}</nav>
      <div className="sidebar-bottom"><div className="sidebar-tip"><span className="tip-icon"><Sparkles size={16} /></span><strong>Small steps add up.</strong><span>Review your numbers regularly to stay close to your goals.</span></div><div className="sidebar-user"><button className="sidebar-profile-trigger" onClick={() => navigate('profile')} title="Open profile"><span className="avatar">{(user.name || user.username).slice(0, 1).toUpperCase()}</span><span className="user-meta"><strong>{user.name}</strong><span>@{user.username}</span></span></button><button className="icon-button logout-button" onClick={onLogout} title="Sign out"><LogOut size={16} /></button></div></div>
    </aside>
    {mobileNavOpen && <button className="mobile-backdrop" onClick={() => setMobileNavOpen(false)} aria-label="Close navigation" />}
    <main className="main-area"><header className="topbar"><div className="topbar-left"><button className="mobile-menu icon-button" onClick={() => setMobileNavOpen(true)} aria-label="Open navigation"><Menu size={20} /></button><div><div className="breadcrumb">Workspace <span>/</span> <strong>{activeMeta.label}</strong></div><h1>{activeMeta.label}</h1></div></div><div className="topbar-actions"><ThemeToggle theme={theme} onToggle={onToggleTheme} /></div></header>
      <div className="page-title-row"><p>{activePage === 'dashboard' ? 'Your financial overview, month by month.' : activePage === 'income' ? 'Track every source of money coming in.' : activePage === 'expenses' ? 'Understand where your money goes.' : activePage === 'limits' ? 'Plan your spending with flexible monthly limits.' : 'Manage your personal information and password.'}</p></div>
      {activePage === 'dashboard' && <DashboardPage month={month} onMonthChange={setMonth} onNavigate={navigate} refreshKey={refreshKey} />}
      {activePage === 'income' && <TransactionPage kind="income" month={month} onMonthChange={setMonth} onChanged={refresh} refreshKey={refreshKey} notify={notify} />}
      {activePage === 'expenses' && <TransactionPage kind="expense" month={month} onMonthChange={setMonth} onChanged={refresh} refreshKey={refreshKey} notify={notify} />}
      {activePage === 'limits' && <ExpenseLimitsPage month={month} onMonthChange={setMonth} refreshKey={refreshKey} onChanged={refresh} notify={notify} />}
      {activePage === 'profile' && <ProfilePage user={user} onUserUpdate={onUserUpdate} notify={notify} />}
      <footer className="app-footer"><span>© {new Date().getFullYear()} Moki</span><span>Made for intentional money habits</span></footer>
    </main><Toast toast={toast} onClose={() => setToast(null)} />
  </div>;
}

function AdminLogin({ onAuthenticated, theme, onToggleTheme }) {
  const [username, setUsername] = useState(''); const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false); const [ready, setReady] = useState(false); const [error, setError] = useState('');
  useEffect(() => { api('/admin/csrf').then(() => setReady(true)).catch((err) => setError(err.message)); }, []);
  async function submit(event) { event.preventDefault(); setBusy(true); setError(''); try { const result = await api('/admin/login', jsonRequest('POST', { username, password })); onAuthenticated(result.admin); } catch (err) { setError(err.message); } finally { setBusy(false); } }
  return <div className="admin-auth-wrap"><div className="admin-auth-theme"><ThemeToggle theme={theme} onToggle={onToggleTheme} /></div><div className="admin-auth-card"><div className="brand"><span className="brand-mark"><MokiMark /></span><span>moki<span className="admin-brand-suffix"> / admin</span></span></div><span className="eyebrow">RESTRICTED AREA</span><h1>Administrator portal</h1><p>Sign in with your administrator credentials to manage Moki.</p><form className="auth-form" onSubmit={submit}><Field label="Administrator username"><input autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} required minLength={3} maxLength={50} /></Field><Field label="Password"><input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} maxLength={128} /></Field>{error && <div className="inline-error">{error}</div>}<Button type="submit" disabled={busy || !ready}>{busy ? <LoaderCircle size={16} className="spin" /> : <ShieldCheck size={16} />} Sign in to admin</Button></form><a className="admin-back-link" href="/">Back to Moki</a></div></div>;
}

function AdminOverview() {
  const [data, setData] = useState(null); const [error, setError] = useState('');
  const load = useCallback(async () => { try { setData(await api('/admin/dashboard')); } catch (err) { setError(err.message); } }, []);
  useEffect(() => { load(); }, [load]);
  if (error) return <div className="panel error-panel">{error}</div>;
  if (!data) return <LoadingBlock label="Loading administrator overview" />;
  const cards = [
    ['Registered users', data.registered_users, Users, 'blue'], ['Active users', data.active_users, UserRound, 'green'],
    ['Inactive users', data.inactive_users, UserRound, 'orange'], ['Deleted accounts', data.deleted_users, Trash2, 'red'],
    ['Administrators', data.administrators, ShieldCheck, 'purple'],
  ];
  return <div className="page-content"><div className="admin-welcome"><div><span className="toolbar-eyebrow">SYSTEM SUMMARY</span><h2>Welcome to Moki administration.</h2><p>Monitor user access and manage the accounts that use your workspace.</p></div><span className="admin-welcome-icon"><ShieldCheck size={27} /></span></div><div className="admin-metric-grid">{cards.map(([label, value, Icon, tone]) => <div className="admin-metric-card" key={label}><span className={`metric-icon metric-${tone}`}><Icon size={18} /></span><small>{label}</small><strong>{value}</strong></div>)}</div><section className="panel admin-quick-panel"><div className="panel-heading"><div><h3>Administration tools</h3><p>Manage user accounts and administrator access.</p></div></div><div className="admin-quick-grid"><button onClick={() => window.dispatchEvent(new CustomEvent('moki-admin-nav', { detail: 'users' }))}><Users size={20} /><span><strong>User Management</strong><small>View users, access status, and account activity.</small></span><ChevronRight size={17} /></button><button onClick={() => window.dispatchEvent(new CustomEvent('moki-admin-nav', { detail: 'administrators' }))}><UserCog size={20} /><span><strong>Administrators</strong><small>Create additional administrator accounts.</small></span><ChevronRight size={17} /></button></div></section></div>;
}

function AdminTransactionDetails({ title, items }) {
  const months = [...new Set(items.map((item) => item.month))].sort().reverse();
  const [month, setMonth] = useState('all');
  useEffect(() => { setMonth('all'); }, [items]);
  const filtered = month === 'all' ? items : items.filter((item) => item.month === month);
  return <section className="admin-finance-detail">
    <div className="admin-finance-heading"><div><strong>{title}</strong><small>{filtered.length} {filtered.length === 1 ? 'entry' : 'entries'} shown</small></div>
      <select aria-label={`Filter ${title} by month`} value={month} onChange={(event) => setMonth(event.target.value)}><option value="all">All months</option>{months.map((value) => <option key={value} value={value}>{formatMonth(value)}</option>)}</select>
    </div>
    {filtered.length === 0 ? <div className="admin-finance-empty">No {title.toLowerCase()} recorded.</div> : <div className="table-scroll admin-finance-table"><table><thead><tr><th>Month</th><th>Description</th><th>Type</th><th className="align-right">Amount</th></tr></thead><tbody>{filtered.map((item) => <tr key={item.id}><td>{formatMonth(item.month)}</td><td><strong>{item.description}</strong></td><td><span className={`type-pill type-${item.type}`}>{item.type}</span></td><td className="align-right amount-cell">{formatMoney(item.amount)}</td></tr>)}</tbody></table></div>}
  </section>;
}

function AdminUsers({ notify }) {
  const [users, setUsers] = useState([]); const [selected, setSelected] = useState(null); const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState(''); const [newPassword, setNewPassword] = useState('');
  const load = useCallback(async () => { setLoading(true); try { const result = await api('/admin/users'); setUsers(result.items); } catch (err) { notify(err.message, 'error'); } finally { setLoading(false); } }, []);
  useEffect(() => { load(); }, [load]);
  async function openUser(id) { try { setSelected(await api(`/admin/users/${id}`)); setNewPassword(''); } catch (err) { notify(err.message, 'error'); } }
  async function updateStatus(action) { try { await api(`/admin/users/${selected.id}/status`, jsonRequest('POST', { action })); notify(action === 'deactivate' ? 'User account deactivated.' : 'User account reactivated.'); await openUser(selected.id); await load(); } catch (err) { notify(err.message, 'error'); } }
  async function resetPassword(event) { event.preventDefault(); if (newPassword.length < 6) { notify('Password must contain at least 6 characters.', 'error'); return; } try { await api(`/admin/users/${selected.id}/password`, jsonRequest('POST', { new_password: newPassword })); setNewPassword(''); notify('User password reset. All existing user sessions were revoked.'); } catch (err) { notify(err.message, 'error'); } }
  async function softDelete() { if (!window.confirm(`Soft-delete ${selected.username}? This action cannot be undone from the admin portal.`)) return; try { await api(`/admin/users/${selected.id}/delete`, jsonRequest('POST', {})); notify('User account soft-deleted.'); setSelected(null); await load(); } catch (err) { notify(err.message, 'error'); } }
  const filtered = users.filter((user) => `${user.name} ${user.username}`.toLowerCase().includes(search.toLowerCase()));
  return <div className="page-content admin-users-layout"><section className="panel table-panel"><div className="panel-heading"><div><h3>User accounts</h3><p>Active and inactive accounts. Deleted accounts are not restorable.</p></div><span className="count-pill">{users.length} users</span></div><div className="admin-search"><Search size={16} /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by name or username" /></div>{loading ? <LoadingBlock label="Loading users" /> : filtered.length === 0 ? <div className="empty-table"><Users size={21} /><strong>No matching users</strong><span>Try another name or username.</span></div> : <div className="table-scroll"><table><thead><tr><th>User</th><th>Status</th><th>Created</th><th /></tr></thead><tbody>{filtered.map((user) => <tr key={user.id}><td><strong>{user.name}</strong><div className="admin-username">@{user.username}</div></td><td><span className={`status-pill ${user.is_active ? 'status-active' : 'status-inactive'}`}>{user.is_active ? 'Active' : 'Inactive'}</span></td><td>{new Date(user.created_at).toLocaleDateString('en-GB')}</td><td><button className="button button-secondary button-small" onClick={() => openUser(user.id)}>View <ChevronRight size={14} /></button></td></tr>)}</tbody></table></div>}</section>
    {selected && <section className="panel admin-user-detail"><div className="panel-heading"><div><span className="toolbar-eyebrow">USER DETAIL</span><h3>{selected.name}</h3><p>@{selected.username} · Joined {new Date(selected.created_at).toLocaleDateString('en-GB')}</p></div><button className="icon-button" onClick={() => setSelected(null)} aria-label="Close detail"><X size={17} /></button></div><div className="user-detail-stats"><div><small>Income entries</small><strong>{selected.income_count}</strong><span>{formatMoney(selected.income_total)}</span></div><div><small>Expense entries</small><strong>{selected.expense_count}</strong><span>{formatMoney(selected.expense_total)}</span></div></div><div className="admin-finance-details"><AdminTransactionDetails title="Income components" items={selected.income_items || []} /><AdminTransactionDetails title="Expense components" items={selected.expense_items || []} /></div><div className="admin-status-line"><span>Account status</span><span className={`status-pill ${selected.is_active ? 'status-active' : 'status-inactive'}`}>{selected.is_active ? 'Active' : 'Inactive'}</span></div><div className="admin-action-row"><Button variant="secondary" onClick={() => updateStatus(selected.is_active ? 'deactivate' : 'reactivate')}>{selected.is_active ? 'Deactivate account' : 'Reactivate account'}</Button></div><form className="admin-reset-form" onSubmit={resetPassword}><Field label="Reset user password"><input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} minLength={6} maxLength={128} placeholder="New password (6+ characters)" required /></Field><Button type="submit" variant="secondary"><KeyRound size={15} /> Reset password</Button></form><div className="admin-danger-zone"><div><strong>Delete user account</strong><small>Soft-delete prevents sign-in. Account data remains preserved.</small></div><Button variant="danger" onClick={softDelete}><Trash2 size={15} /> Soft delete</Button></div></section>}
  </div>;
}

function AdminAdministrators({ notify }) {
  const [items, setItems] = useState([]); const [loading, setLoading] = useState(true); const [saving, setSaving] = useState(false);
  const [username, setUsername] = useState(''); const [password, setPassword] = useState(''); const [confirmPassword, setConfirmPassword] = useState('');
  const load = useCallback(async () => { setLoading(true); try { const result = await api('/admin/administrators'); setItems(result.items); } catch (err) { notify(err.message, 'error'); } finally { setLoading(false); } }, []);
  useEffect(() => { load(); }, [load]);
  async function create(event) { event.preventDefault(); if (password.length < 6) { notify('Administrator password must contain at least 6 characters.', 'error'); return; } if (password !== confirmPassword) { notify('Password confirmation does not match.', 'error'); return; } setSaving(true); try { await api('/admin/administrators', jsonRequest('POST', { username, password, confirm_password: confirmPassword })); notify('Administrator account created.'); setUsername(''); setPassword(''); setConfirmPassword(''); await load(); } catch (err) { notify(err.message, 'error'); } finally { setSaving(false); } }
  return <div className="page-content"><section className="panel"><div className="panel-heading"><div><h3>Create administrator</h3><p>Grant separate administrative access to a trusted operator.</p></div><span className="bulk-badge"><ShieldCheck size={13} /> ADMIN ACCESS</span></div><form className="admin-create-form" onSubmit={create}><Field label="Username"><input value={username} onChange={(e) => setUsername(e.target.value)} minLength={3} maxLength={50} pattern="[a-zA-Z0-9_]{3,50}" placeholder="admin_username" required /></Field><Field label="Password" hint="At least 6 characters for administrator accounts."><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={6} maxLength={128} required /></Field><Field label="Confirm password"><input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} minLength={6} maxLength={128} required /></Field><Button type="submit" disabled={saving}>{saving ? <LoaderCircle size={16} className="spin" /> : <Plus size={16} />} Create administrator</Button></form></section><section className="panel table-panel"><div className="panel-heading"><div><h3>Administrator accounts</h3><p>Administrative accounts are not deactivated or deleted from this portal.</p></div><span className="count-pill">{items.length} administrators</span></div>{loading ? <LoadingBlock label="Loading administrators" /> : <div className="table-scroll"><table><thead><tr><th>Username</th><th>Role</th><th>Created</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td><strong>@{item.username}</strong></td><td><span className="status-pill status-active">Administrator</span></td><td>{new Date(item.created_at).toLocaleDateString('en-GB')}</td></tr>)}</tbody></table></div>}</section></div>;
}

function AdminProfilePage({ admin, onAdminUpdate, notify }) {
  const [username, setUsername] = useState(admin.username || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [saving, setSaving] = useState(false);
  useEffect(() => { setUsername(admin.username || ''); setCurrentPassword(''); setNewPassword(''); setConfirmPassword(''); }, [admin.id, admin.username]);

  async function save(event) {
    event.preventDefault();
    if (newPassword && newPassword.length < 6) { notify('New password must contain at least 6 characters.', 'error'); return; }
    if (newPassword && newPassword !== confirmPassword) { notify('New password confirmation does not match.', 'error'); return; }
    if (newPassword && !currentPassword) { notify('Enter your current password to change it.', 'error'); return; }
    setSaving(true);
    try {
      const result = await api('/admin/profile', jsonRequest('PATCH', {
        username: username.trim(), ...(newPassword ? { current_password: currentPassword, new_password: newPassword } : {}),
      }));
      onAdminUpdate(result.admin); setCurrentPassword(''); setNewPassword(''); setConfirmPassword('');
      notify(newPassword ? 'Administrator profile and password updated.' : 'Administrator profile updated.');
    } catch (err) { notify(err.message, 'error'); }
    finally { setSaving(false); }
  }

  return <div className="page-content profile-page"><section className="panel profile-panel">
    <div className="panel-heading"><div><h3>Administrator profile</h3><p>Update the username and password used to access this portal.</p></div><span className="bulk-badge"><ShieldCheck size={13} /> ADMIN PROFILE</span></div>
    <form className="profile-form admin-profile-form" onSubmit={save}>
      <Field label="Username"><input value={username} onChange={(event) => setUsername(event.target.value)} minLength={3} maxLength={50} pattern="[a-zA-Z0-9_]{3,50}" required /></Field>
      <div className="profile-section-divider"><span>Password</span><small>Leave the new password fields blank to keep your current password.</small></div>
      <Field label="Current password"><input type="password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} autoComplete="current-password" maxLength={128} placeholder="Required only when changing password" /></Field>
      <Field label="New password"><input type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} autoComplete="new-password" minLength={6} maxLength={128} placeholder="At least 6 characters" /></Field>
      <Field label="Confirm new password"><input type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} autoComplete="new-password" minLength={6} maxLength={128} placeholder="Re-enter new password" /></Field>
      <div className="profile-form-actions"><Button type="submit" disabled={saving}>{saving ? <LoaderCircle size={16} className="spin" /> : <Check size={16} />} Save changes</Button></div>
    </form>
  </section></div>;
}

function AdminPortal({ onBackToApp, theme, onToggleTheme }) {
  const [admin, setAdmin] = useState(null); const [checking, setChecking] = useState(true); const [activePage, setActivePage] = useState('dashboard');
  const [mobileNavOpen, setMobileNavOpen] = useState(false); const [toast, setToast] = useState(null);
  const notify = (message, type = 'success') => { setToast({ message, type }); window.clearTimeout(notify.timeout); notify.timeout = window.setTimeout(() => setToast(null), 4200); };
  useEffect(() => { api('/admin/me').then((result) => setAdmin(result.admin)).catch(() => setAdmin(null)).finally(() => setChecking(false)); }, []);
  useEffect(() => { const handler = (event) => setActivePage(event.detail); window.addEventListener('moki-admin-nav', handler); return () => window.removeEventListener('moki-admin-nav', handler); }, []);
  async function logout() { try { await api('/admin/logout', { method: 'POST' }); } catch { /* Session may already have expired. */ } setAdmin(null); }
  if (checking) return <div className="boot-screen"><div className="boot-logo"><MokiMark /></div><span>Preparing administrator portal…</span><LoaderCircle size={17} className="spin" /></div>;
  if (!admin) return <><AdminLogin onAuthenticated={setAdmin} theme={theme} onToggleTheme={onToggleTheme} /><Toast toast={toast} onClose={() => setToast(null)} /></>;
  const activeMeta = ADMIN_NAV.find((item) => item.id === activePage) || ADMIN_NAV[0];
  return <div className="app-shell admin-shell"><aside className={`sidebar ${mobileNavOpen ? 'sidebar-open' : ''}`}><div className="sidebar-brand"><div className="brand"><span className="brand-mark"><MokiMark /></span><span>moki</span></div><span className="brand-caption">ADMINISTRATION</span></div><div className="sidebar-section-label">CONTROL PANEL</div><nav className="side-nav">{ADMIN_NAV.map(({ id, label, icon: Icon }) => <button key={id} className={`nav-item ${activePage === id ? 'nav-active' : ''}`} onClick={() => { setActivePage(id); setMobileNavOpen(false); }}><Icon size={18} /><span>{label}</span>{activePage === id && <i />}</button>)}</nav><div className="sidebar-bottom"><button className="admin-back-workspace" onClick={onBackToApp}><ArrowUpRight size={15} /> Open Moki workspace</button><div className="sidebar-user"><button className="sidebar-profile-trigger" onClick={() => { setActivePage('profile'); setMobileNavOpen(false); }} title="Open administrator profile"><span className="avatar"><ShieldCheck size={15} /></span><span className="user-meta"><strong>{admin.username}</strong><span>Administrator</span></span></button><button className="icon-button logout-button" onClick={logout} title="Sign out"><LogOut size={16} /></button></div></div></aside>{mobileNavOpen && <button className="mobile-backdrop" onClick={() => setMobileNavOpen(false)} aria-label="Close navigation" />}<main className="main-area"><header className="topbar"><div className="topbar-left"><button className="mobile-menu icon-button" onClick={() => setMobileNavOpen(true)} aria-label="Open navigation"><Menu size={20} /></button><div><div className="breadcrumb">Moki <span>/</span> <strong>Admin</strong></div><h1>{activeMeta.label}</h1></div></div><div className="topbar-actions"><span className="admin-identity"><ShieldCheck size={15} /> {admin.username}</span><ThemeToggle theme={theme} onToggle={onToggleTheme} /></div></header><div className="page-title-row"><p>Manage Moki accounts and administrator access.</p></div>{activePage === 'dashboard' && <AdminOverview />}{activePage === 'users' && <AdminUsers notify={notify} />}{activePage === 'administrators' && <AdminAdministrators notify={notify} />}{activePage === 'profile' && <AdminProfilePage admin={admin} onAdminUpdate={setAdmin} notify={notify} />}<footer className="app-footer"><span>© {new Date().getFullYear()} Moki Administration</span><span>Restricted access</span></footer></main><Toast toast={toast} onClose={() => setToast(null)} /></div>;
}

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  const [authError, setAuthError] = useState('');
  const [theme, setTheme] = useState(() => {
    try { const saved = window.localStorage.getItem('moki-theme'); return saved === 'light' ? 'light' : 'dark'; }
    catch { return 'dark'; }
  });
  const isAdminRoute = window.location.pathname === '/admin' || window.location.pathname.startsWith('/admin/');

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { window.localStorage.setItem('moki-theme', theme); } catch { /* Private browsing may disable storage. */ }
  }, [theme]);

  useEffect(() => {
    if (isAdminRoute) { setChecking(false); return undefined; }
    let mounted = true;
    api('/auth/me').then((result) => {
      if (mounted) { setUser(result.user); if (result.user.theme === 'light' || result.user.theme === 'dark') setTheme(result.user.theme); }
    }).catch((err) => { if (mounted && ![401, 403].includes(err.status)) setAuthError(err.message); }).finally(() => { if (mounted) setChecking(false); });
    return () => { mounted = false; };
  }, [isAdminRoute]);

  function toggleTheme() {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    if (user && !isAdminRoute) {
      const updated = { ...user, theme: next };
      setUser(updated);
      api('/auth/theme', jsonRequest('PATCH', { theme: next })).catch((err) => setAuthError(err.message));
    }
  }

  async function logout() { try { await api('/auth/logout', { method: 'POST' }); } catch { /* Clear local state even when the session has expired. */ } setUser(null); }
  if (isAdminRoute) return <AdminPortal onBackToApp={() => { window.location.href = '/'; }} theme={theme} onToggleTheme={toggleTheme} />;
  if (checking) return <div className="boot-screen"><div className="boot-logo"><MokiMark /></div><span>Preparing your workspace…</span><LoaderCircle size={17} className="spin" /></div>;
  if (!user) return <><AuthScreen onAuthenticated={(nextUser) => { setUser(nextUser); }} theme={theme} onToggleTheme={toggleTheme} />{authError && <div className="auth-startup-note">API connection: {authError}</div>}</>;
  return <AppShell user={user} onLogout={logout} onUserUpdate={setUser} theme={theme} onToggleTheme={toggleTheme} />;
}
