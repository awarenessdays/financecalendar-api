//+------------------------------------------------------------------+
//| FinanceCalendarNewsFilter                                        |
//| Example Expert Advisor: shows whether the chart symbol is inside |
//| a quiet window around a scheduled economic release.              |
//| Data: Finance Calendar API, https://www.financecalendar.com/api/ |
//+------------------------------------------------------------------+
// Release 0.2.0. Consult the package README for compile and runtime acceptance evidence.
//
// This program places, changes and closes no orders. It does two things:
//   1. Shows the next release and the current state on the chart.
//   2. Publishes the state as a terminal global variable, FC_NEWS_BLOCK_<symbol>
//      (1 = inside a quiet window, 0 = clear, -1 = no usable schedule), so another
//      Expert Advisor can read it with GlobalVariableGet() without including any code.
//
// Setup:
//   1. Put this file and FinanceCalendarNews.mqh in the same Experts folder and compile.
//   2. Tools > Options > Expert Advisors > Allow WebRequest for listed URL:
//         https://www.financecalendar.com
//   3. Attach to a chart and enter your API key. Do not share a preset that contains it.
#property strict
#include "FinanceCalendarNews.mqh"

input string InpApiKey         = "";      // Finance Calendar API key
input string InpStateTag       = "";      // Optional namespace; one publisher per symbol/tag
input string InpImpact         = "high";  // Release impact: high, or high,medium
input int    InpMinutesBefore  = 30;      // Quiet window before a release (minutes)
input int    InpMinutesAfter   = 30;      // Quiet window after a release (minutes)
input int    InpRefreshMinutes = 180;     // Paid-plan refresh every 3 hours
input int    InpMaxEvents      = 500;     // Maximum records; truncation is unknown

string StateSuffix() { return _Symbol + (InpStateTag == "" ? "" : "_" + InpStateTag); }
string StateName() { return "FC_NEWS_BLOCK_" + StateSuffix(); }
string StateTimeName() { return "FC_NEWS_AT_" + StateSuffix(); }

void Show()
{
   string reason;
   int state = FcNewsState(_Symbol, InpMinutesBefore, InpMinutesAfter, reason);
   GlobalVariableSet(StateName(), (double)state);
   GlobalVariableSet(StateTimeName(), (double)TimeGMT());
   string text = "Finance Calendar news filter: " + _Symbol + "\n";
   if(state == FC_NEWS_UNKNOWN) text += "UNKNOWN: " + reason + "\n";
   else if(state == FC_NEWS_QUIET) text += "QUIET WINDOW: " + reason + "\n";
   else text += "Outside the configured news window\n";
   datetime when;
   string name;
   if(FcNewsNext(_Symbol, when, name))
      text += "Next: " + name + " at " + TimeToString(when, TIME_DATE | TIME_MINUTES) + " UTC\n";
   else if(state != FC_NEWS_UNKNOWN) text += "No further releases for this symbol in the loaded schedule\n";
   text += "State: " + StateName() + "\nSchedule: financecalendar.com";
   Comment(text);
}

int OnInit()
{
   if(StringLen(InpStateTag) > 12 || StringLen(StateName()) > 63) return INIT_PARAMETERS_INCORRECT;
   for(int i = 0; i < StringLen(InpStateTag); i++)
   {
      ushort c = StringGetCharacter(InpStateTag, i);
      if(!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || FcJsonDigit(c) || c == '_' || c == '-')) return INIT_PARAMETERS_INCORRECT;
   }
   FcNewsInit(InpApiKey, InpImpact, InpRefreshMinutes, InpMaxEvents);
   EventSetTimer(30);
   FcNewsRefresh();
   Show();
   return INIT_SUCCEEDED;
}

void OnTimer()
{
   FcNewsRefresh();
   Show();
}

void OnTick() {}

void OnDeinit(const int reason)
{
   EventKillTimer();
   GlobalVariableDel(StateName());
   GlobalVariableDel(StateTimeName());
   Comment("");
}
