//+------------------------------------------------------------------+
//| FinanceCalendarNewsFilter                                        |
//| Example Expert Advisor: shows whether the chart symbol is inside |
//| a quiet window around a scheduled economic release.              |
//| Data: Finance Calendar API, https://www.financecalendar.com/api/ |
//+------------------------------------------------------------------+
// Compiles in MetaEditor for MQL4 and MQL5; not run on a trading terminal by the publisher.
// Test it on a demo account before relying on it.
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
input string InpImpact         = "high";  // Release impact: high, or high,medium
input int    InpMinutesBefore  = 30;      // Quiet window before a release (minutes)
input int    InpMinutesAfter   = 30;      // Quiet window after a release (minutes)
input int    InpRefreshMinutes = 180;     // Schedule refresh (180 fits Free Developer)
input int    InpMaxEvents      = 20;      // Releases per request (20 on Free Developer)

string StateName() { return "FC_NEWS_BLOCK_" + _Symbol; }

void Show()
{
   string reason;
   bool blocked = FcNewsBlocked(_Symbol, InpMinutesBefore, InpMinutesAfter, reason);
   bool ready = FcNewsReady();
   GlobalVariableSet(StateName(), ready ? (blocked ? 1.0 : 0.0) : -1.0);
   string text = "Finance Calendar news filter: " + _Symbol + "\n";
   if(!ready) text += "No usable schedule. " + FcNewsStatus() + "\n";
   else if(blocked) text += "QUIET WINDOW: " + reason + "\n";
   else text += "Clear\n";
   datetime when;
   string name;
   if(FcNewsNext(_Symbol, when, name))
      text += "Next: " + name + " at " + TimeToString(when, TIME_DATE | TIME_MINUTES) + " UTC\n";
   else if(ready) text += "No further releases for this symbol in the loaded schedule\n";
   text += "Schedule: financecalendar.com";
   Comment(text);
}

int OnInit()
{
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
   Comment("");
}
