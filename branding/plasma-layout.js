var allPanels = panels();
for (var panelIndex = 0; panelIndex < allPanels.length; panelIndex++) {
    var panelWidgets = allPanels[panelIndex].widgets();
    for (var widgetIndex = 0; widgetIndex < panelWidgets.length; widgetIndex++) {
        var widget = panelWidgets[widgetIndex];
        if (widget.type === "org.kde.plasma.kickoff" || widget.type === "org.kde.plasma.kicker") {
            widget.currentConfigGroup = ["General"];
            widget.writeConfig("icon", "najs");
        }
    }
}
