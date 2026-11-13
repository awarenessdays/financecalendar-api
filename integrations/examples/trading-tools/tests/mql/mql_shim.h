// Stand-in for the MetaTrader runtime, enough to run the news-filter source as C++.
// It checks parsing and decision logic offline. It is not a MetaEditor compile.
#pragma once
#include <algorithm>
#include <cstdio>
#include <ctime>
#include <map>
#include <sstream>
#include <string>
#include <vector>
typedef std::string string;
typedef unsigned short ushort;
typedef unsigned char uchar;
typedef unsigned int uint;
typedef unsigned long long ulong;
typedef long long datetime;
template <class T> struct Array {
   std::vector<T> v;
   T &operator[](int i) { return v.at(i); }
};
#define input
enum { FILE_READ = 1, FILE_WRITE = 2, FILE_BIN = 4, FILE_SHARE_READ = 8, CP_UTF8 = 65001, INVALID_HANDLE = -1,
       TIME_DATE = 1, TIME_MINUTES = 2, SYMBOL_CURRENCY_BASE = 1, SYMBOL_CURRENCY_PROFIT = 2, INIT_SUCCEEDED = 0 };
// --- test controls ---
static datetime t_now = 0;
static int t_status = 200, t_requests = 0, t_error = 0;
static string t_body, t_headers, t_url, t_request_headers, t_comment, t_symbol = "EURUSD";
static std::map<string, double> t_globals;
static std::map<string, string> t_files;
static std::map<string, std::pair<string, string>> t_symbols;
static std::vector<string> t_log;
static string _Symbol = "EURUSD";
// --- runtime ---
inline int StringLen(const string &s) { return (int)s.size(); }
inline ushort StringGetCharacter(const string &s, int i) { return (i < 0 || i >= (int)s.size()) ? 0 : (uchar)s[i]; }
inline string StringSubstr(const string &s, int start, int len = -1) {
   if(start < 0 || start >= (int)s.size()) return "";
   return len < 0 ? s.substr(start) : s.substr(start, len);
}
inline int StringReplace(string &s, const string &a, const string &b) {
   int n = 0; size_t p = 0;
   while(!a.empty() && (p = s.find(a, p)) != string::npos) { s.replace(p, a.size(), b); p += b.size(); n++; }
   return n;
}
inline bool StringToUpper(string &s) { for(auto &c : s) c = (char)toupper((uchar)c); return true; }
inline bool StringToLower(string &s) { for(auto &c : s) c = (char)tolower((uchar)c); return true; }
inline int StringFind(const string &s, const string &sub, int start = 0) { size_t p = s.find(sub, start); return p == string::npos ? -1 : (int)p; }
inline int StringSplit(const string &s, ushort sep, Array<string> &out) {
   out.v.clear(); std::stringstream ss(s); string part;
   while(std::getline(ss, part, (char)sep)) out.v.push_back(part);
   return (int)out.v.size();
}
inline long long StringToInteger(const string &s) { return atoll(s.c_str()); }
inline string IntegerToString(long long n) { return std::to_string(n); }
inline string TimeToString(datetime t, int flags = TIME_DATE | TIME_MINUTES) {
   time_t tt = (time_t)t; struct tm g; gmtime_r(&tt, &g); char buf[32]; string out;
   if(flags & TIME_DATE) { strftime(buf, sizeof buf, "%Y.%m.%d", &g); out += buf; }
   if(flags & TIME_MINUTES) { strftime(buf, sizeof buf, "%H:%M", &g); out += (out.empty() ? "" : " "); out += buf; }
   return out;
}
inline datetime StringToTime(const string &s) {
   struct tm g = {}; if(sscanf(s.c_str(), "%d.%d.%d %d:%d", &g.tm_year, &g.tm_mon, &g.tm_mday, &g.tm_hour, &g.tm_min) < 3) return 0;
   g.tm_year -= 1900; g.tm_mon -= 1; return (datetime)timegm(&g);
}
inline datetime TimeGMT() { return t_now; }
inline bool GlobalVariableCheck(const string &n) { return t_globals.count(n) > 0; }
inline double GlobalVariableGet(const string &n) { return t_globals.count(n) ? t_globals[n] : 0; }
inline datetime GlobalVariableSet(const string &n, double v) { t_globals[n] = v; return t_now; }
inline bool GlobalVariableDel(const string &n) { return t_globals.erase(n) > 0; }
static std::map<int, std::pair<string, int>> t_handles; static int t_next = 1;
inline int FileOpen(const string &name, int flags) {
   if((flags & FILE_READ) && !t_files.count(name)) return INVALID_HANDLE;
   if(flags & FILE_WRITE) t_files[name] = "";
   t_handles[t_next] = {name, flags}; return t_next++;
}
inline ulong FileSize(int h) { return t_files[t_handles[h].first].size(); }
template <class T> inline uint FileReadArray(int h, Array<T> &a, int start, int count) {
   const string &d = t_files[t_handles[h].first]; a.v.assign(d.begin(), d.begin() + std::min((size_t)count, d.size())); return (uint)a.v.size();
}
template <class T> inline uint FileWriteArray(int h, Array<T> &a, int start, int count) {
   t_files[t_handles[h].first].assign(a.v.begin() + start, a.v.begin() + start + count); return (uint)count;
}
inline void FileClose(int h) { t_handles.erase(h); }
inline bool FileDelete(const string &n) { return t_files.erase(n) > 0; }
template <class T> inline string CharArrayToString(Array<T> &a, int start = 0, int count = -1, int cp = 0) {
   return string(a.v.begin() + start, count < 0 ? a.v.end() : a.v.begin() + start + count);
}
template <class T> inline int ArrayResize(Array<T> &a, int n, int reserve = 0) { a.v.resize(n); return n; }
template <class T> inline int ArraySize(Array<T> &a) { return (int)a.v.size(); }
inline void ResetLastError() {}
inline int GetLastError() { return t_error; }
inline int WebRequest(const string &method, const string &url, const string &headers, int timeout, Array<char> &req, Array<char> &res, string &res_headers) {
   t_requests++; t_url = url; t_request_headers = headers;
   if(t_status == -1) return -1;
   res.v.assign(t_body.begin(), t_body.end()); res_headers = t_headers; return t_status;
}
inline string SymbolInfoString(const string &symbol, int which) {
   auto it = t_symbols.find(symbol); if(it == t_symbols.end()) return "";
   return which == SYMBOL_CURRENCY_BASE ? it->second.first : it->second.second;
}
template <class... A> inline void Print(A... a) { std::ostringstream o; (void)std::initializer_list<int>{(o << a, 0)...}; t_log.push_back(o.str()); }
inline void Comment(const string &s) { t_comment = s; }
inline bool EventSetTimer(int) { return true; }
inline void EventKillTimer() {}
