/* SPDX-License-Identifier: GPL-3.0-or-later */
import QtQuick 2.15
import calamares.slideshow 1.0

Presentation {
    id: presentation

    function nextSlide() { presentation.goToNextSlide() }
    function onActivate() { presentation.currentSlide = 0 }
    function onLeave() {}

    Timer {
        interval: 9000
        running: presentation.activatedInCalamares
        repeat: true
        onTriggered: presentation.nextSlide()
    }

    Slide {
        FeatureSlide {
            anchors.fill: parent
            kicker: "BUILT ON ARCH LINUX"
            title: "A clean system, shaped around you"
            body: "Najs combines current upstream packages with a focused desktop and carefully selected defaults."
            accent: "#55d6be"
        }
    }
    Slide {
        FeatureSlide {
            anchors.fill: parent
            kicker: "YOUR WORKFLOW"
            title: "Choose the desktop that fits"
            body: "Plasma, GNOME, Hyprland, Xfce, and Cinnamon are available from one consistent installer."
            accent: "#67b7ff"
        }
    }
    Slide {
        FeatureSlide {
            anchors.fill: parent
            kicker: "PRIVATE BY DEFAULT"
            title: "Modern storage and encryption"
            body: "Use Btrfs generation roots, LUKS2 encryption, or advanced manual partitioning with clear review steps."
            accent: "#a98bff"
        }
    }
    Slide {
        FeatureSlide {
            anchors.fill: parent
            kicker: "READY FOR REAL WORK"
            title: "From gaming to development"
            body: "Install curated software collections without spending the first hour rebuilding your setup."
            accent: "#ffb86b"
        }
    }

    component FeatureSlide: Rectangle {
        property string kicker
        property string title
        property string body
        property color accent
        color: "#0b1722"

        Rectangle {
            width: 7
            height: parent.height * 0.64
            radius: 4
            color: parent.accent
            anchors.left: parent.left
            anchors.leftMargin: 72
            anchors.verticalCenter: parent.verticalCenter
        }
        Column {
            width: parent.width - 210
            spacing: 18
            anchors.left: parent.left
            anchors.leftMargin: 110
            anchors.verticalCenter: parent.verticalCenter
            Text { text: parent.parent.kicker; color: parent.parent.accent; font.pixelSize: 15; font.bold: true; font.letterSpacing: 2 }
            Text { width: parent.width; text: parent.parent.title; color: "#f4fbff"; font.pixelSize: 34; font.bold: true; wrapMode: Text.WordWrap }
            Text { width: parent.width; text: parent.parent.body; color: "#9fb4c2"; font.pixelSize: 18; lineHeight: 1.35; wrapMode: Text.WordWrap }
        }
    }
}
