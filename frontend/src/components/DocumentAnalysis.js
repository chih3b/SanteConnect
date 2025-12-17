import { useState, useRef, useEffect } from "react";
import {
  Upload,
  FileText,
  AlertTriangle,
  Loader,
  Brain,
  Activity,
  TrendingUp,
  TrendingDown,
  ChevronDown,
  ChevronUp,
  Phone,
  BarChart3,
  PieChart,
  Calendar,
  Users,
  RefreshCw,
  CheckCircle,
  XCircle,
  Smartphone,
  Save,
  TestTube,
} from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart as RechartsPie,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const MANE_API = "http://localhost:8004";
const COLORS = ["#667eea", "#764ba2", "#2ecc71", "#f39c12", "#e74c3c"];

export default function DocumentAnalysis() {
  const [activeView, setActiveView] = useState("analysis"); // "analysis" or "dashboard"
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [resumeText, setResumeText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  
  // Dashboard state
  const [stats, setStats] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [recentAnalyses, setRecentAnalyses] = useState([]);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  
  // SMS state
  const [doctorPhone, setDoctorPhone] = useState("+21654708360");
  const [smsStatus, setSmsStatus] = useState(null);
  const [showSmsPanel, setShowSmsPanel] = useState(false);
  
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setDashboardLoading(true);
    try {
      const [statsRes, chartsRes, analysesRes] = await Promise.all([
        fetch(`${MANE_API}/api/dashboard/stats`),
        fetch(`${MANE_API}/api/dashboard/charts`),
        fetch(`${MANE_API}/api/analyses?limit=10`),
      ]);

      if (statsRes.ok) setStats(await statsRes.json());
      if (chartsRes.ok) setChartData(await chartsRes.json());
      if (analysesRes.ok) {
        const data = await analysesRes.json();
        setRecentAnalyses(data.analyses || []);
      }
    } catch (e) {
      console.error("Dashboard fetch error:", e);
    } finally {
      setDashboardLoading(false);
    }
  };


  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
      if (selectedFile.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = (e) => setPreview(e.target.result);
        reader.readAsDataURL(selectedFile);
      } else {
        setPreview(null);
      }
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      setError(null);
      if (droppedFile.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = (e) => setPreview(e.target.result);
        reader.readAsDataURL(droppedFile);
      }
    }
  };

  const analyzeDocument = async () => {
    if (!file && !resumeText.trim()) {
      setError("Veuillez uploader un document ou entrer un résumé médical");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      let response;
      if (file) {
        const formData = new FormData();
        formData.append("file", file);
        if (resumeText) formData.append("resume_texte", resumeText);

        response = await fetch(`${MANE_API}/api/analysis/image`, {
          method: "POST",
          body: formData,
        });
      } else {
        response = await fetch(`${MANE_API}/api/analysis`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ resume_texte: resumeText }),
        });
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Analyse échouée");
      }

      const data = await response.json();
      setResult(data);
      fetchDashboardData(); // Refresh dashboard after analysis
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const saveDoctorPhone = async () => {
    if (!doctorPhone.startsWith("+")) {
      setSmsStatus({ type: "error", message: "Format: +21612345678" });
      return;
    }
    try {
      const res = await fetch(`${MANE_API}/api/doctor-phone`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone: doctorPhone }),
      });
      if (res.ok) {
        setSmsStatus({ type: "success", message: "Numéro enregistré!" });
      }
    } catch (e) {
      setSmsStatus({ type: "error", message: "Erreur de sauvegarde" });
    }
    setTimeout(() => setSmsStatus(null), 3000);
  };

  const testSMS = async () => {
    if (!doctorPhone.startsWith("+")) {
      setSmsStatus({ type: "error", message: "Format: +21612345678" });
      return;
    }
    try {
      setSmsStatus({ type: "loading", message: "Envoi en cours..." });
      const res = await fetch(`${MANE_API}/api/test-sms`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone: doctorPhone }),
      });
      if (res.ok) {
        setSmsStatus({ type: "success", message: "SMS de test envoyé!" });
      } else {
        throw new Error("Échec envoi");
      }
    } catch (e) {
      setSmsStatus({ type: "error", message: "Erreur d'envoi SMS" });
    }
    setTimeout(() => setSmsStatus(null), 3000);
  };

  const getScoreColor = (score) => {
    if (score <= 15) return "text-green-600 bg-green-100";
    if (score <= 30) return "text-amber-600 bg-amber-100";
    if (score <= 50) return "text-orange-600 bg-orange-100";
    return "text-red-600 bg-red-100";
  };

  const getUrgencyColor = (urgency) => {
    if (urgency === "faible") return "bg-green-100 text-green-700 border-green-200";
    if (urgency === "moyenne") return "bg-amber-100 text-amber-700 border-amber-200";
    return "bg-red-100 text-red-700 border-red-200";
  };

  const resetForm = () => {
    setFile(null);
    setPreview(null);
    setResumeText("");
    setResult(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };


  // Stats Card Component
  const StatCard = ({ icon: Icon, title, value, label, trend, color = "blue" }) => (
    <div className="bg-card rounded-xl p-4 border border-border shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <div className={`text-2xl font-bold text-${color}-600`}>{value}</div>
          <div className="text-sm text-muted-foreground">{title}</div>
          {label && <div className="text-xs text-muted-foreground mt-1">{label}</div>}
        </div>
        <div className={`w-12 h-12 bg-${color}-100 rounded-xl flex items-center justify-center`}>
          <Icon className={`w-6 h-6 text-${color}-600`} />
        </div>
      </div>
      {trend && (
        <div className={`mt-2 text-xs flex items-center gap-1 ${trend.includes("Hausse") ? "text-green-600" : "text-red-600"}`}>
          {trend.includes("Hausse") ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          {trend}
        </div>
      )}
    </div>
  );

  // Chart Card Component
  const ChartCard = ({ title, icon: Icon, children }) => (
    <div className="bg-card rounded-xl border border-border shadow-sm overflow-hidden">
      <div className="p-4 border-b border-border flex items-center gap-2">
        <Icon className="w-5 h-5 text-purple-600" />
        <h3 className="font-semibold text-foreground">{title}</h3>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );

  return (
    <div className="h-full overflow-y-auto p-4 sm:p-6 bg-muted">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header with View Toggle */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg">
              <Brain className="w-7 h-7 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-foreground">Mané - Analyse Médicale</h2>
              <p className="text-muted-foreground text-sm">OCR + IA pour évaluer les risques</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="bg-card rounded-lg p-1 border border-border flex">
              <button
                onClick={() => setActiveView("analysis")}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  activeView === "analysis" ? "bg-purple-600 text-white" : "text-muted-foreground hover:bg-muted"
                }`}
              >
                <FileText className="w-4 h-4 inline mr-2" />
                Analyse
              </button>
              <button
                onClick={() => setActiveView("dashboard")}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  activeView === "dashboard" ? "bg-purple-600 text-white" : "text-muted-foreground hover:bg-muted"
                }`}
              >
                <BarChart3 className="w-4 h-4 inline mr-2" />
                Dashboard
              </button>
            </div>
            
            <button
              onClick={fetchDashboardData}
              className="p-2 bg-card border border-border rounded-lg hover:bg-muted"
              title="Rafraîchir"
            >
              <RefreshCw className={`w-5 h-5 text-muted-foreground ${dashboardLoading ? "animate-spin" : ""}`} />
            </button>
            
            <button
              onClick={() => setShowSmsPanel(!showSmsPanel)}
              className={`p-2 border rounded-lg ${showSmsPanel ? "bg-purple-100 border-purple-300" : "bg-card border-border hover:bg-muted"}`}
              title="Configuration SMS"
            >
              <Smartphone className={`w-5 h-5 ${showSmsPanel ? "text-purple-600" : "text-muted-foreground"}`} />
            </button>
          </div>
        </div>

        {/* SMS Configuration Panel */}
        {showSmsPanel && (
          <div className="bg-card rounded-xl border border-border p-4 shadow-sm">
            <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
              <Phone className="w-5 h-5 text-purple-600" />
              Notifications SMS Médecin
            </h3>
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                value={doctorPhone}
                onChange={(e) => setDoctorPhone(e.target.value)}
                placeholder="+21672345678"
                className="flex-1 px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
              <button
                onClick={saveDoctorPhone}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                Enregistrer
              </button>
              <button
                onClick={testSMS}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
              >
                <TestTube className="w-4 h-4" />
                Tester SMS
              </button>
            </div>
            {smsStatus && (
              <div className={`mt-3 p-3 rounded-lg flex items-center gap-2 ${
                smsStatus.type === "success" ? "bg-green-100 text-green-700" :
                smsStatus.type === "error" ? "bg-red-100 text-red-700" :
                "bg-blue-100 text-blue-700"
              }`}>
                {smsStatus.type === "success" && <CheckCircle className="w-4 h-4" />}
                {smsStatus.type === "error" && <XCircle className="w-4 h-4" />}
                {smsStatus.type === "loading" && <Loader className="w-4 h-4 animate-spin" />}
                {smsStatus.message}
              </div>
            )}
          </div>
        )}


        {/* DASHBOARD VIEW */}
        {activeView === "dashboard" && (
          <div className="space-y-6">
            {/* Stats Grid */}
            {stats && (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                  icon={FileText}
                  title="Analyses Totales"
                  value={stats.total_analyses || 0}
                  label={`${stats.analyses_this_week || 0} cette semaine`}
                  color="blue"
                />
                <StatCard
                  icon={Activity}
                  title="Score Moyen"
                  value={`${stats.average_score || 0}%`}
                  trend={stats.trend}
                  color="amber"
                />
                <StatCard
                  icon={AlertTriangle}
                  title="Cas à Haut Risque"
                  value={stats.high_risk_count || 0}
                  label={`${stats.avg_risks_per_analysis || 0} risques/analyse`}
                  color="red"
                />
                <StatCard
                  icon={Calendar}
                  title="Aujourd'hui"
                  value={stats.today_count || 0}
                  label={`${stats.analyses_this_month || 0} ce mois`}
                  color="green"
                />
              </div>
            )}

            {/* Charts Grid */}
            {chartData && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Daily Activity Chart */}
                <ChartCard title="Activité des 7 derniers jours" icon={BarChart3}>
                  {chartData.daily_counts?.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={chartData.daily_counts}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                        <XAxis dataKey="date" stroke="#999" />
                        <YAxis stroke="#999" />
                        <Tooltip />
                        <Bar dataKey="count" fill="#667eea" radius={[8, 8, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                      Aucune donnée disponible
                    </div>
                  )}
                </ChartCard>

                {/* Score Evolution Chart */}
                <ChartCard title="Évolution des Scores" icon={TrendingUp}>
                  {chartData.score_evolution?.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                      <LineChart data={chartData.score_evolution}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                        <XAxis dataKey="index" stroke="#999" />
                        <YAxis stroke="#999" />
                        <Tooltip />
                        <Line type="monotone" dataKey="score" stroke="#3498db" strokeWidth={2} dot={{ fill: "#3498db", r: 4 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                      Aucune donnée disponible
                    </div>
                  )}
                </ChartCard>

                {/* Risk Distribution Pie Chart */}
                <ChartCard title="Distribution des Risques" icon={PieChart}>
                  {chartData.risk_distribution?.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                      <RechartsPie>
                        <Pie
                          data={chartData.risk_distribution}
                          dataKey="count"
                          nameKey="level"
                          cx="50%"
                          cy="50%"
                          outerRadius={80}
                          label={({ name, value }) => `${value}`}
                        >
                          {chartData.risk_distribution.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </RechartsPie>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                      Aucune donnée disponible
                    </div>
                  )}
                </ChartCard>

                {/* Diagnosis Distribution */}
                <ChartCard title="Diagnostics Fréquents" icon={Users}>
                  {chartData.diagnosis_distribution?.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={chartData.diagnosis_distribution} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                        <XAxis type="number" stroke="#999" />
                        <YAxis dataKey="diagnosis" type="category" stroke="#999" width={120} tick={{ fontSize: 12 }} />
                        <Tooltip />
                        <Bar dataKey="count" fill="#764ba2" radius={[0, 8, 8, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                      Aucune donnée disponible
                    </div>
                  )}
                </ChartCard>
              </div>
            )}

            {/* Recent Analyses Table */}
            <div className="bg-card rounded-xl border border-border shadow-sm overflow-hidden">
              <div className="p-4 border-b border-border flex items-center gap-2">
                <Activity className="w-5 h-5 text-purple-600" />
                <h3 className="font-semibold text-foreground">Dernières Analyses</h3>
              </div>
              {recentAnalyses.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-muted">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">ID</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Diagnostic</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Score</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Risques</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {recentAnalyses.slice().reverse().map((analysis) => (
                        <tr key={analysis.id} className="hover:bg-muted">
                          <td className="px-4 py-3 font-medium text-foreground">#{analysis.id}</td>
                          <td className="px-4 py-3 text-muted-foreground max-w-xs truncate">{analysis.diagnostic?.substring(0, 40)}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getScoreColor(analysis.score)}`}>
                              {analysis.score}%
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <span className="flex items-center gap-1 text-muted-foreground">
                              <AlertTriangle className="w-4 h-4 text-amber-500" />
                              {analysis.risks_count}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-8 text-center text-muted-foreground">
                  Aucune analyse pour le moment.
                </div>
              )}
            </div>
          </div>
        )}


        {/* ANALYSIS VIEW */}
        {activeView === "analysis" && (
          <div className="space-y-6">
            {/* Upload Area */}
            {!result && (
              <div className="bg-card rounded-2xl shadow-lg border border-border p-6">
                <div
                  onClick={() => fileInputRef.current?.click()}
                  onDrop={handleDrop}
                  onDragOver={(e) => e.preventDefault()}
                  className="border-2 border-dashed border-border rounded-xl p-8 text-center cursor-pointer hover:border-purple-400 hover:bg-purple-50/50 transition-all"
                >
                  {preview ? (
                    <div>
                      <img src={preview} alt="Preview" className="max-h-48 mx-auto rounded-lg shadow-md mb-4" />
                      <p className="text-green-600 font-medium">{file?.name}</p>
                    </div>
                  ) : (
                    <>
                      <Upload className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-foreground mb-2">Glissez-déposez votre document</h3>
                      <p className="text-muted-foreground text-sm">Image (JPG, PNG) ou PDF</p>
                      {file && <p className="text-green-600 mt-2 font-medium">{file.name}</p>}
                    </>
                  )}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*,.pdf"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </div>

                <div className="mt-6">
                  <label className="block text-sm font-medium text-foreground mb-2">
                    <FileText className="w-4 h-4 inline mr-2" />
                    Résumé additionnel (optionnel)
                  </label>
                  <textarea
                    value={resumeText}
                    onChange={(e) => setResumeText(e.target.value)}
                    placeholder="Ajoutez des informations complémentaires..."
                    className="w-full p-4 border border-border rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none h-32"
                  />
                </div>

                {error && (
                  <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5" />
                    {error}
                  </div>
                )}

                <button
                  onClick={analyzeDocument}
                  disabled={loading || (!file && !resumeText.trim())}
                  className="w-full mt-6 py-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-xl font-semibold hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg"
                >
                  {loading ? (
                    <>
                      <Loader className="w-5 h-5 animate-spin" />
                      Analyse en cours...
                    </>
                  ) : (
                    <>
                      <Brain className="w-5 h-5" />
                      Lancer l'analyse IA
                    </>
                  )}
                </button>
              </div>
            )}

            {/* Results */}
            {result && (
              <div className="space-y-6">
                {/* Extracted Text Card (from OCR) */}
                {result.extracted_text && (
                  <div className="bg-card rounded-2xl shadow-lg border border-border overflow-hidden">
                    <button
                      onClick={() => setShowDetails(!showDetails)}
                      className="w-full p-4 flex items-center justify-between text-left hover:bg-muted"
                    >
                      <span className="font-medium text-foreground flex items-center gap-2">
                        <FileText className="w-5 h-5 text-blue-600" />
                        Texte Extrait (OCR)
                        <span className="text-xs text-muted-foreground ml-2">Méthode: {result.ocr_method}</span>
                      </span>
                      {showDetails ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                    </button>
                    {showDetails && (
                      <div className="p-4 border-t border-border bg-muted">
                        <pre className="text-sm text-muted-foreground whitespace-pre-wrap font-mono max-h-48 overflow-auto">{result.extracted_text}</pre>
                      </div>
                    )}
                  </div>
                )}

                {/* Score Card */}
                {result.analyse_complete?.score_rehospitalisation && (
                  <div className="bg-card rounded-2xl shadow-lg border border-border p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-purple-600" />
                        Risque de Réhospitalisation
                      </h3>
                      <span className={`text-3xl font-bold px-4 py-2 rounded-xl ${getScoreColor(parseInt(result.analyse_complete.score_rehospitalisation))}`}>
                        {result.analyse_complete.score_rehospitalisation}
                      </span>
                    </div>
                    {result.analyse_complete.explication_score && (
                      <p className="text-muted-foreground text-sm">{result.analyse_complete.explication_score}</p>
                    )}
                  </div>
                )}

                {/* Diagnosis Card */}
                {result.analyse_complete?.diagnostic_principal && (
                  <div className="bg-card rounded-2xl shadow-lg border border-border p-6">
                    <h3 className="text-lg font-semibold text-foreground flex items-center gap-2 mb-4">
                      <Activity className="w-5 h-5 text-blue-600" />
                      Diagnostic Principal
                    </h3>
                    <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
                      <p className="text-blue-800 font-medium text-lg">{result.analyse_complete.diagnostic_principal}</p>
                      {result.analyse_complete.explication_diagnostic && (
                        <p className="text-blue-600 text-sm mt-2">{result.analyse_complete.explication_diagnostic}</p>
                      )}
                    </div>
                  </div>
                )}

                {/* Red Flags */}
                {result.analyse_complete?.drapeaux_rouges?.length > 0 && (
                  <div className="bg-card rounded-2xl shadow-lg border border-border p-6">
                    <h3 className="text-lg font-semibold text-foreground flex items-center gap-2 mb-4">
                      <AlertTriangle className="w-5 h-5 text-red-600" />
                      Alertes Cliniques ({result.analyse_complete.drapeaux_rouges.length})
                    </h3>
                    <div className="space-y-3">
                      {result.analyse_complete.drapeaux_rouges.map((flag, idx) => (
                        <div key={idx} className={`p-4 rounded-xl border ${getUrgencyColor(flag.urgence)}`}>
                          <div className="flex items-start justify-between">
                            <div>
                              <p className="font-medium">{flag.risque}</p>
                              {flag.source_donnees && (
                                <p className="text-sm opacity-75 mt-1">Source: {flag.source_donnees}</p>
                              )}
                            </div>
                            <span className="text-xs font-semibold uppercase px-2 py-1 rounded-full bg-card/50">
                              {flag.urgence}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Medical Synthesis */}
                {result.synthese_medecin && (
                  <div className="bg-card rounded-2xl shadow-lg border border-border p-6">
                    <h3 className="text-lg font-semibold text-foreground flex items-center gap-2 mb-4">
                      <FileText className="w-5 h-5 text-green-600" />
                      Synthèse Médicale
                    </h3>
                    <div className="bg-green-50 rounded-xl p-4 border border-green-200">
                      <p className="text-foreground whitespace-pre-wrap leading-relaxed">{result.synthese_medecin}</p>
                    </div>
                  </div>
                )}

                {/* New Analysis Button */}
                <button
                  onClick={resetForm}
                  className="w-full py-4 bg-muted text-foreground rounded-xl font-semibold hover:bg-muted flex items-center justify-center gap-2"
                >
                  <Upload className="w-5 h-5" />
                  Nouvelle Analyse
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
