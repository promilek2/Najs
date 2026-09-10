/*
 * SPDX-FileCopyrightText: 2020 Adriaan de Groot <groot@kde.org>
 * SPDX-FileCopyrightText: 2021 Anke Boersma <demm@kaosx.us>
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

import io.calamares.ui 1.0
import io.calamares.core 1.0
import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    color: Branding.styleString(Branding.SidebarBackground)
    height: 50
    width: parent.width

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 12
        anchors.rightMargin: 12
        spacing: 4

        Image {
            Layout.preferredWidth: 32
            Layout.preferredHeight: 32
            Layout.rightMargin: 8
            source: "file:/" + Branding.imagePath(Branding.ProductLogo)
            fillMode: Image.PreserveAspectFit
        }

        Repeater {
            model: ViewManager
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 34
                radius: 9
                color: index === ViewManager.currentStepIndex
                    ? Branding.styleString(Branding.SidebarBackgroundCurrent)
                    : "transparent"

                Text {
                    anchors.fill: parent
                    anchors.margins: 3
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                    text: display
                    color: index === ViewManager.currentStepIndex
                        ? Branding.styleString(Branding.SidebarTextCurrent)
                        : Branding.styleString(Branding.SidebarText)
                    font.pixelSize: 11
                    font.weight: index === ViewManager.currentStepIndex ? Font.DemiBold : Font.Normal
                }
            }
        }
    }
}
